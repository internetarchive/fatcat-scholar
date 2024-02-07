import elasticsearch
import fatcat_openapi_client

from scholar.config import settings
from scholar.issue_db import IssueDB


def test_issue_db_basics() -> None:
    api_conf = fatcat_openapi_client.Configuration()
    api_conf.host = settings.FATCAT_API_HOST
    api = fatcat_openapi_client.DefaultApi(fatcat_openapi_client.ApiClient(api_conf))

    es_client = elasticsearch.Elasticsearch(settings.ELASTICSEARCH_FATCAT_BASE)

    issue_db = IssueDB(settings.SCHOLAR_ISSUEDB_PATH)
    issue_db.init_db()

    with open("tests/files/sim_collections.json", "r") as f:
        issue_db.load_pubs(f.readlines(), api)

    with open("tests/files/sim_items.json", "r") as f:
        issue_db.load_issues(f.readlines(), es_client)
