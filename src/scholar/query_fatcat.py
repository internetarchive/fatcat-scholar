import argparse
import json
import os
import sys
from typing import Any

import elasticsearch
from elasticsearch_dsl import Q, Search

from scholar.sandcrawler import requests_retry_session


def run_query_fatcat(query: str, fulltext_only: bool, json_output: Any) -> None:
    """
    Queries fatcat search index (the full regular fatcat.wiki release index)
    for search string passed (and some filters), iterates over the result set
    (using scroll), and fetches full release entity (via api.fatcat.wik) for
    each.

    TODO: group by work_id
    """
    api_session = requests_retry_session()

    es_backend = os.environ.get(
        "ELASTICSEARCH_FATCAT_BASE", "https://search.fatcat.wiki"
    )
    es_index = os.environ.get("ELASTICSEARCH_FATCAT_RELEASE_INDEX", "fatcat_release")
    es_client = elasticsearch.Elasticsearch(es_backend)

    search = Search(using=es_client, index=es_index)

    search = search.exclude("terms", release_type=["stub", "component", "abstract"])

    # "Emerald Expert Briefings"
    search = search.exclude("terms", container_id=["fnllqvywjbec5eumrbavqipfym"])

    # ResearchGate
    search = search.exclude("terms", doi_prefix=["10.13140"])

    if fulltext_only:
        search = search.filter("terms", in_ia=True)

    search = search.query(
        Q("query_string", query=query, default_operator="AND", fields=["biblio"])
    )

    print(f"Expecting {search.count()} search hits", file=sys.stderr)

    search = search.params(clear_scroll=False)
    search = search.params(_source=False)

    results = search.scan()
    for hit in results:
        release_id = hit.meta.id
        resp = api_session.get(
            f"https://api.fatcat.wiki/v0/release/{release_id}",
            params={
                "expand": "container,files,filesets,webcaptures",
                "hide": "references",
            },
        )
        resp.raise_for_status()
        row = dict(
            fatcat_hit=hit.meta._d_,
            release_id=release_id,
            fatcat_release=resp.json(),
        )
        print(json.dumps(row, sort_keys=True), file=json_output)


def main() -> None:
    """
    Run this command like:

        python -m scholar.query_fatcat
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "query",
        help="base query string to use",
        type=str,
    )
    parser.add_argument(
        "--fulltext-only",
        help="flag to filter to only documents with fulltext available",
        action="store_true",
    )

    args = parser.parse_args()

    run_query_fatcat(args.query, args.fulltext_only, sys.stdout)


if __name__ == "__main__":
    main()
