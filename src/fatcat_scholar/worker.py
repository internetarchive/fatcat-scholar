import argparse
import datetime
import os
import sys
from typing import Any, List

import elasticsearch
import elasticsearch.helpers
import fatcat_openapi_client
import requests
import sentry_sdk

from fatcat_scholar.config import GIT_REVISION, settings
from fatcat_scholar.issue_db import IssueDB
from fatcat_scholar.kafka import KafkaWorker
from fatcat_scholar.sandcrawler import (
    SandcrawlerMinioClient,
    SandcrawlerPostgrestClient,
)
from fatcat_scholar.schema import IntermediateBundle
from fatcat_scholar.sim_pipeline import SimPipeline
from fatcat_scholar.transform import transform_heavy
from fatcat_scholar.work_pipeline import WorkPipeline


class FetchDocsWorker(KafkaWorker):
    def __init__(
        self,
        work_pipeline: WorkPipeline,
        sim_pipeline: SimPipeline,
        produce_docs_topic: str,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.sim_pipeline = sim_pipeline
        self.work_pipeline = work_pipeline
        api_conf = fatcat_openapi_client.Configuration()
        api_conf.host = kwargs.get("fatcat_api_host", "https://api.fatcat.wiki/v0")
        self.fatcat_api = fatcat_openapi_client.DefaultApi(
            fatcat_openapi_client.ApiClient(api_conf)
        )
        self.producer = self.create_kafka_producer(self.kafka_brokers)
        self.produce_topic = produce_docs_topic
        print(f"Will produce bundles to: {self.produce_topic}", file=sys.stderr)

    def process_msg(self, msg: dict) -> None:
        key = msg["key"]
        if key.startswith("work_") and msg.get("work_ident"):
            stubs = self.fatcat_api.get_work_releases(
                ident=msg["work_ident"],
                hide="abstracts,references",
            )
            full_releases = []
            for r in stubs:
                full = self.fatcat_api.get_release(
                    r.ident,
                    expand="container,files,filesets,webcaptures",
                    hide="references",
                )
                full_releases.append(full)
            if not full_releases:
                return
            bundle = self.work_pipeline.process_release_list(full_releases)
            bundle.fetched = datetime.datetime.utcnow()
            self.producer.produce(
                self.produce_topic,
                bundle.json(exclude_none=True).encode("UTF-8"),
                key=key,
                on_delivery=self._fail_fast_produce,
            )
            self.counts["works-produced"] += 1

            # check for errors etc
            self.producer.poll(0)
        elif key.startswith("sim_"):
            # filter out "contents" and "index" items (again)
            if msg["issue_item"].endswith("_contents") or msg["issue_item"].endswith(
                "_index"
            ):
                return
            try:
                full_issue = self.sim_pipeline.fetch_sim_issue(
                    msg["issue_item"], msg["pub_collection"]
                )
            except requests.exceptions.ConnectionError as e:
                print(str(e), file=sys.stderr)
                raise e
            except requests.exceptions.ReadTimeout as e:
                print(str(e), file=sys.stderr)
                raise e
            if not full_issue:
                return
            pages = self.sim_pipeline.full_issue_to_pages(full_issue)
            for bundle in pages:
                bundle.fetched = datetime.datetime.utcnow()
                self.producer.produce(
                    self.produce_topic,
                    bundle.json(exclude_none=True).encode("UTF-8"),
                    # NOTE: this isn't going to be the document key, but it will sort by issue
                    key=key,
                    on_delivery=self._fail_fast_produce,
                )
                self.counts["pages-produced"] += 1

            # check for errors etc
            self.producer.poll(0)
        else:
            raise NotImplementedError(f"can't process updated for key={key}")


class IndexDocsWorker(KafkaWorker):
    def __init__(self, es_client: Any, es_index: str, **kwargs: Any):
        super().__init__(**kwargs)
        self.es_client = es_client
        self.es_index = es_index

    def process_batch(self, batch: List[dict]) -> None:
        bulk_actions = []
        for obj in batch:
            bundle = IntermediateBundle.from_json(obj)
            assert bundle.doc_type
            es_doc = transform_heavy(bundle)
            if not es_doc:
                continue
            else:
                bulk_actions.append(
                    {
                        "_index": self.es_index,
                        "_op_type": "index",
                        "_id": es_doc.key,
                        "_source": es_doc.json(exclude_none=True, sort_keys=True),
                    }
                )
                self.counts["docs-indexed"] += 1

        if not bulk_actions:
            return

        elasticsearch.helpers.bulk(self.es_client, bulk_actions, timeout="50s")
        self.counts["batches-indexed"] += 1


def main() -> None:
    """
    Run this command like:

        python -m fatcat_scholar.work_pipeline
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers()

    parser.add_argument(
        "--issue-db-file",
        help="sqlite3 database file to open",
        default=settings.SCHOLAR_ISSUEDB_PATH,
        type=str,
    )
    parser.add_argument(
        "--sandcrawler-db-api",
        help="Sandcrawler Postgrest API endpoint",
        default=settings.SANDCRAWLER_DB_API,
        type=str,
    )
    parser.add_argument(
        "--sandcrawler-s3-api",
        help="Sandcrawler S3 (minio/seaweedfs) API endpoint",
        default=settings.SANDCRAWLER_S3_API,
        type=str,
    )

    sub = subparsers.add_parser(
        "fetch-docs-worker",
    )
    sub.set_defaults(worker="fetch-docs-worker")

    sub = subparsers.add_parser(
        "index-docs-worker",
    )
    sub.set_defaults(worker="index-docs-worker")

    args = parser.parse_args()
    if not args.__dict__.get("worker"):
        parser.print_help(file=sys.stderr)
        sys.exit(-1)

    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SCHOLAR_ENV,
            max_breadcrumbs=10,
            release=GIT_REVISION,
        )

    if args.worker == "fetch-docs-worker":
        issue_db = IssueDB(args.issue_db_file)
        wp = WorkPipeline(
            issue_db=issue_db,
            sandcrawler_db_client=SandcrawlerPostgrestClient(
                api_url=args.sandcrawler_db_api
            ),
            sandcrawler_s3_client=SandcrawlerMinioClient(
                host_url=args.sandcrawler_s3_api,
                access_key=os.environ.get("MINIO_ACCESS_KEY"),
                secret_key=os.environ.get("MINIO_SECRET_KEY"),
            ),
        )
        sp = SimPipeline(issue_db=issue_db)
        fdw = FetchDocsWorker(
            kafka_brokers=settings.KAFKA_BROKERS,
            consume_topics=[
                f"fatcat-{settings.SCHOLAR_ENV}.work-ident-updates",
                # TODO: f"scholar-{settings.SCHOLAR_ENV}.sim-updates",
            ],
            consumer_group=f"scholar-{settings.SCHOLAR_ENV}-fetch-workers",
            work_pipeline=wp,
            sim_pipeline=sp,
            produce_docs_topic=f"scholar-{settings.SCHOLAR_ENV}.update-docs",
            fatcat_api_host=settings.FATCAT_API_HOST,
        )
        fdw.run()
    elif args.worker == "index-docs-worker":
        es_client = elasticsearch.Elasticsearch(
            settings.ELASTICSEARCH_WRITE_BASE, timeout=50.0
        )
        idw = IndexDocsWorker(
            kafka_brokers=settings.KAFKA_BROKERS,
            batch_size=settings.INDEX_WORKER_BATCH_SIZE,
            consume_topics=[f"scholar-{settings.SCHOLAR_ENV}.update-docs"],
            consumer_group=f"scholar-{settings.SCHOLAR_ENV}-index-workers",
            es_client=es_client,
            es_index=settings.ELASTICSEARCH_WRITE_FULLTEXT_INDEX,
        )
        idw.run()


if __name__ == "__main__":
    main()
