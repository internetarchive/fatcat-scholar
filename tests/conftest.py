#import elasticsearch
from datetime import datetime
import pytest
#from dotenv import load_dotenv
import fatcat_openapi_client as fcapi
from fastapi.testclient import TestClient

from scholar.web import app

#import fatcat_web

#ES_CONTAINER_STATS_RESP = {
#    "timed_out": False,
#    "aggregations": {
#        "container_stats": {
#            "buckets": {
#                "is_preserved": {"doc_count": 461939},
#                "in_kbart": {"doc_count": 461939},
#                "in_web": {"doc_count": 2797},
#            }
#        },
#        "preservation": {
#            "buckets": [
#                {"key": "bright", "doc_count": 444},
#                {"key": "dark", "doc_count": 111},
#            ],
#            "sum_other_doc_count": 0,
#        },
#        "release_type": {
#            "buckets": [
#                {"key": "article-journal", "doc_count": 456},
#                {"key": "book", "doc_count": 123},
#            ],
#            "sum_other_doc_count": 0,
#        },
#    },
#    "hits": {"total": 461939, "hits": [], "max_score": 0.0},
#    "_shards": {"successful": 5, "total": 5, "skipped": 0, "failed": 0},
#    "took": 50,
#}
#
## TODO: this should not be empty
#ES_CONTAINER_RANDOM_RESP = {
#    "timed_out": False,
#    "hits": {"total": 461939, "hits": [], "max_score": 0.0},
#    "_shards": {"successful": 5, "total": 5, "skipped": 0, "failed": 0},
#    "took": 50,
#}
#
#ES_RELEASE_EMPTY_RESP = {
#    "timed_out": False,
#    "hits": {"total": 0, "hits": [], "max_score": 0.0},
#    "_shards": {"successful": 5, "total": 5, "skipped": 0, "failed": 0},
#    "took": 50,
#}
#
#
#@pytest.fixture
#def full_app(mocker):
#    load_dotenv(dotenv_path="./example.env")
#    fatcat_web.app.testing = True
#    fatcat_web.app.debug = False
#    fatcat_web.app.config["WTF_CSRF_ENABLED"] = False
#
#    # mock out ES client requests, so they at least fail fast
#    fatcat_web.app.es_client = elasticsearch.Elasticsearch("mockbackend")
#    mocker.patch("elasticsearch.connection.Urllib3HttpConnection.perform_request")
#    return fatcat_web.app

@pytest.fixture
def client():
    return TestClient(app)

#@pytest.fixture
#def api():
#    load_dotenv(dotenv_path="./example.env")
#    api_client = authenticated_api("http://localhost:9411/v0")
#    api_client.editor_id = "aaaaaaaaaaaabkvkaaaaaaaaae"
#    return api_client
#
#
#@pytest.fixture
#def api_dummy_entities(api):
#    """
#    This is a sort of bleh fixture. Should probably create an actual
#    object/class with create/accept/clean-up methods?
#    """
#
#    c1 = CreatorEntity(display_name="test creator deletion")
#    j1 = ContainerEntity(name="test journal deletion")
#    r1 = ReleaseEntity(title="test release creator deletion", ext_ids=ReleaseExtIds())
#    f1 = FileEntity()
#    fs1 = FilesetEntity()
#    wc1 = WebcaptureEntity(
#        timestamp="2000-01-01T12:34:56Z",
#        original_url="http://example.com/",
#    )
#
#    eg = quick_eg(api)
#    c1 = api.get_creator(api.create_creator(eg.editgroup_id, c1).ident)
#    j1 = api.get_container(api.create_container(eg.editgroup_id, j1).ident)
#    r1 = api.get_release(api.create_release(eg.editgroup_id, r1).ident)
#    w1 = api.get_work(r1.work_id)
#    f1 = api.get_file(api.create_file(eg.editgroup_id, f1).ident)
#    fs1 = api.get_fileset(api.create_fileset(eg.editgroup_id, fs1).ident)
#    wc1 = api.get_webcapture(api.create_webcapture(eg.editgroup_id, wc1).ident)
#
#    return {
#        "api": api,
#        "editgroup": eg,
#        "creator": c1,
#        "container": j1,
#        "file": f1,
#        "fileset": fs1,
#        "webcapture": wc1,
#        "release": r1,
#        "work": w1,
#    }
#
#
#def test_get_changelog_entry(api):
#    """Check that fixture is working"""
#    cl = api.get_changelog_entry(1)
#    assert cl
#
#
### Helpers ##################################################################
#
#
#def quick_eg(api_inst):
#    eg = api_inst.create_editgroup(fatcat_openapi_client.Editgroup())
#    return eg

@pytest.fixture
def basic_entities():
    return {
        "release": fcapi.ReleaseEntity(
            state="active",
            title="steel and lace",
            release_stage="published",
            publisher="a deadly combination",
            ext_ids=fcapi.ReleaseExtIds(),
            pages="1-60",
            volume="99",
            refs=[],
            contribs=[],
            abstracts=[]),
        "container": fcapi.ContainerEntity(
            name="urusei yatsura studies"),
        "creator": fcapi.CreatorEntity(
            display_name="testuo the iron man",
            given_name="tetsuo",
            surname="the iron man"),
        "file": fcapi.FileEntity(
            size=66,
            md5="f013d66c7f6817d08b7eb2a93e6d0440",
            sha256="a77e4c11a57f1d757fca5754a8f83b5d4ece49a2d28596889127c1a2f3f28832",
            release_ids=[],
            releases=[],
            ),
        "fileset": fcapi.FilesetEntity(
            manifest=[
                fcapi.FilesetFile(
                    size=66,
                    md5="a013166c7f6817808b7eb2a93e6d0640",
                    sha256="b75e1c10a57f2d757fca5754a8f83b5d4ece49a2d28596889127c1a2f3f28833",
                    path="cool.txt",
                    sha1="443f1867b3a56132905e8d611ad03445d8134d3c",
                    )
                ],
            releases=[],
            release_ids=[],
            ),
        "webcapture": fcapi.WebcaptureEntity(
            state="active",
            archive_urls=[],
            cdx=[
                fcapi.WebcaptureCdxLine(
                    surt="org,archive,scholar)/",
                    timestamp=datetime.utcnow(),
                    url="https://scholar.archive.org/",
                    sha1="443f1867b3a56132905e8d611ad03445d8134d3c",
                )],
            releases=[],
            ),
        "work": fcapi.WorkEntity(
            state="active",

            ),
    }
