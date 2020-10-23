from fatcat_scholar.issue_db import IssueDB
from fatcat_scholar.sandcrawler import (
    SandcrawlerPostgrestClient,
    SandcrawlerMinioClient,
)
from fatcat_scholar.work_pipeline import *
from fatcat_scholar.config import settings


def test_run_transform() -> None:

    issue_db = IssueDB(settings.SCHOLAR_ISSUEDB_PATH)
    issue_db.init_db()

    wp = WorkPipeline(
        issue_db=issue_db,
        sandcrawler_db_client=SandcrawlerPostgrestClient(
            api_url=settings.SANDCRAWLER_DB_API
        ),
        sandcrawler_s3_client=SandcrawlerMinioClient(
            host_url=settings.SANDCRAWLER_S3_API
        ),
    )

    with open("tests/files/release_hsmo6p4smrganpb3fndaj2lon4_sans.json", "r") as f:
        wp.run_releases(f.readlines())
