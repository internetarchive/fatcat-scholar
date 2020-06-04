import io
import sys
import sqlite3
import argparse
from typing import List, Dict, Optional, Any

import requests
import internetarchive

from fatcat_scholar.djvu import djvu_extract_leaf_texts
from fatcat_scholar.issue_db import IssueDB
from fatcat_scholar.schema import (
    DocType,
    IntermediateBundle,
)


def truncate_pub_meta(full: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes a complete archive.org metadata dictionary for a publication
    collection, and simplifies it by removing fields. Motivation is to make
    intermediate bundle files smaller.
    """
    full.pop("files")
    if "ulrichs" in full and full["ulrichs"]:
        full["ulrichs"][0].pop("reviews_mfl")
        full["ulrichs"][0].pop("editorial_description")

        # these are interesting, but just too long
        full["ulrichs"][0].pop("online_availability_full_text")
        full["ulrichs"][0].pop("abstracting_indexing")
        full["ulrichs"][0].pop("publisher_and_ordering_details")
    return full


def truncate_issue_meta(full: Dict[str, Any]) -> Dict[str, Any]:
    """
    Same as truncate_pub_meta() but for issue item metadata
    """
    full.pop("files")
    return full


class SimPipeline:
    def __init__(self, issue_db: IssueDB):
        self.issue_db: IssueDB = issue_db
        self.ia_client = internetarchive.get_session()

    def fetch_sim_issue(self, issue_db_row: Any) -> Optional[Any]:
        """
        issue_item
        pages: str
        page_texts: list
            raw_text
            page_num
            leaf_num
        release_ident: Optional[str]
        pub_item_metadata
        issue_item_metadata
        """
        # fetch full metadata from API
        issue_meta = self.ia_client.get_metadata(issue_db_row["issue_item"])
        pub_meta = self.ia_client.get_metadata(issue_db_row["pub_collection"])

        leaf_index = dict()
        leaf_list = []
        if not "page_numbers" in issue_meta:
            # TODO: warn
            return None
        for entry in issue_meta["page_numbers"].get("pages", []):
            page_num = entry["pageNumber"]
            leaf_index[entry["leafNum"]] = page_num
            if not (page_num and page_num.isdigit()):
                continue
            page_num = int(page_num)
            leaf_list.append(entry["leafNum"])

        if not leaf_list:
            return None

        page_texts: List[Dict[str, Any]] = []
        issue_item = self.ia_client.get_item(issue_db_row["issue_item"])
        issue_item_djvu = issue_item.get_file(issue_db_row["issue_item"] + "_djvu.xml")

        # override 'close()' method so we can still read out contents
        djvu_bytes = io.BytesIO()
        djvu_bytes.close = lambda: None  # type: ignore
        assert issue_item_djvu.download(fileobj=djvu_bytes)
        djvu_bytes.seek(0)
        djvu_xml = io.StringIO(djvu_bytes.read().decode("UTF-8"))
        del djvu_bytes

        leaf_dict = djvu_extract_leaf_texts(djvu_xml)

        for leaf_num, raw_text in leaf_dict.items():
            page_texts.append(
                dict(
                    page_num=leaf_index.get(leaf_num),
                    leaf_num=leaf_num,
                    raw_text=raw_text,
                )
            )

        return dict(
            issue_item=issue_db_row["issue_item"],
            pages=None,
            page_texts=page_texts,
            release_ident=None,
            pub_item_metadata=truncate_pub_meta(pub_meta),
            issue_item_metadata=truncate_issue_meta(issue_meta),
        )

    def run_issue_db(self, limit: int = None):
        count = 0
        self.issue_db.db.row_factory = sqlite3.Row
        cur = self.issue_db.db.cursor()
        for row in cur.execute(
            "SELECT * FROM sim_issue LEFT JOIN sim_pub ON sim_issue.sim_pubid = sim_pub.sim_pubid WHERE sim_issue.release_count < 3"
        ):
            # filter out "contents" and "index" items
            # TODO: more filters; also redundant with IssueDB code?
            if row["issue_item"].endswith("_contents") or row["issue_item"].endswith(
                "_index"
            ):
                continue
            try:
                full_issue = self.fetch_sim_issue(row)
            except requests.exceptions.ConnectionError as e:
                print(str(e), file=sys.stderr)
                continue
            except requests.exceptions.ReadTimeout as e:
                print(str(e), file=sys.stderr)
                continue
            if not full_issue:
                continue
            for leaf in full_issue["page_texts"]:
                bundle = IntermediateBundle(
                    doc_type=DocType.sim_page,
                    releases=[],
                    biblio_release_ident=None,
                    grobid_fulltext=None,
                    pdftotext_fulltext=None,
                    sim_fulltext=dict(
                        issue_item=full_issue["issue_item"],
                        pages=str(leaf["page_num"]),
                        page_texts=[leaf],
                        release_ident=None,
                        pub_item_metadata=full_issue["pub_item_metadata"],
                        issue_item_metadata=full_issue["issue_item_metadata"],
                    ),
                )
                print(bundle.json())
                count += 1
                if limit is not None and count >= limit:
                    break
            if limit is not None and count >= limit:
                break


def main():
    """
    Run this command like:

        python -m fatcat_scholar.sim_pipeline
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers()

    parser.add_argument(
        "--issue-db-file",
        help="sqlite3 database file to open",
        default="data/issue_db.sqlite",
        type=str,
    )

    sub = subparsers.add_parser("run_issue_db", help="iterates through entire IssueDB")
    sub.set_defaults(func="run_issue_db")
    sub.add_argument("--limit", help="maximum number of pages to index", type=int)

    args = parser.parse_args()
    if not args.__dict__.get("func"):
        print("tell me what to do! (try --help)")
        sys.exit(-1)

    sp = SimPipeline(issue_db=IssueDB(args.issue_db_file))

    if args.func == "run_issue_db":
        sp.run_issue_db(limit=args.limit)
    else:
        func = getattr(sp, args.func)
        func()


if __name__ == "__main__":
    main()
