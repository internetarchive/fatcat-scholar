import datetime
import json

from fastapi.testclient import TestClient
import fatcat_openapi_client as fcapi
import pytest

from scholar.web import app

ES_CONTAINER_STATS_RESP = {
    "timed_out": False,
    "aggregations": {
        "container_stats": {
            "buckets": {
                "is_preserved": {"doc_count": 461939},
                "in_kbart": {"doc_count": 461939},
                "in_web": {"doc_count": 2797},
            }
        },
        "preservation": {
            "buckets": [
                {"key": "bright", "doc_count": 444},
                {"key": "dark", "doc_count": 111},
            ],
            "sum_other_doc_count": 0,
        },
        "release_type": {
            "buckets": [
                {"key": "article-journal", "doc_count": 456},
                {"key": "book", "doc_count": 123},
            ],
            "sum_other_doc_count": 0,
        },
    },
    "hits": {"total": 461939, "hits": [], "max_score": 0.0},
    "_shards": {"successful": 5, "total": 5, "skipped": 0, "failed": 0},
    "took": 50,
}

ES_CONTAINER_RANDOM_RESP = {
    # TODO: this should not be empty
    "timed_out": False,
    "hits": {"total": 461939, "hits": [], "max_score": 0.0},
    "_shards": {"successful": 5, "total": 5, "skipped": 0, "failed": 0},
    "took": 50,
}

#ES_RELEASE_EMPTY_RESP = {
#    "timed_out": False,
#    "hits": {"total": 0, "hits": [], "max_score": 0.0},
#    "_shards": {"successful": 5, "total": 5, "skipped": 0, "failed": 0},
#    "took": 50,
#}

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def entity_types():
    return ["release", "work", "webcapture", "file", "fileset", "creator", "container"]


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

@pytest.fixture
def fcclient(mocker):
    mm = mocker.MagicMock()
    mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)
    return mm

@pytest.fixture
def es(mocker):
    return mocker.patch("elasticsearch.connection.Urllib3HttpConnection.perform_request")

@pytest.fixture
def entities():
    return {
        "release": fcapi.ReleaseEntity(
            state="active",
            title="steel and lace",
            release_stage="published",
            publisher="a deadly combination",
            ident="aney5kqnxvbwnn3aasq7uvup6m",
            ext_ids=fcapi.ReleaseExtIds(
                doi="10.1038/35036653",
                wikidata_qid="Q47657205",
                pmid="11034187",
                pmcid="PMC93932",
                isbn13="978-3-16-148410-0",
                jstor="92492",
                ark="ark:/2349/sddd92",
                arxiv="0706.0001v1",
                hdl="20.500.12690/RIN/IDDOAH/BTNH25",
            ),
            pages="1-60",
            volume="99",
            refs=[],
            contribs=[],
            abstracts=[]),
        "container": fcapi.ContainerEntity(
            state="active",
            ident="bi7rkf2w6jc5fd6z2szjd4k7j4",
            name="urusei yatsura studies",
            issne="2148-6905",
            issnp="0084-7887",
            issnl="1790-8426",
            wikidata_qid="Q50815517"),
        "creator": fcapi.CreatorEntity(
            display_name="testuo the iron man",
            given_name="tetsuo",
            ident="iimvc523xbhqlav6j3sbthuehu",
            orcid="0000-0003-3118-6859",
            revision="52444283-850c-41d5-945b-bd7c6112cb89",
            state="active",
            wikidata_qid="Q6251482",
            surname="the iron man"),
        "file": fcapi.FileEntity(
            size=66,
            md5="f013d66c7f6817d08b7eb2a93e6d0440",
            sha1="3d0755107a3fc2b81d0a3886477b5000747512fd",
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
                    timestamp=datetime.datetime.now(datetime.UTC),
                    url="https://scholar.archive.org/",
                    sha1="443f1867b3a56132905e8d611ad03445d8134d3c",
                )],
            releases=[],
            ),
        "work": fcapi.WorkEntity(
            state="active",
            ),
    }

@pytest.fixture
def es_resps():
    with open("tests/cat/files/elastic_refs_in_release.json") as f:
        elastic_resp_in = json.loads(f.read())
    with open("tests/cat/files/elastic_refs_out_release.json") as f:
        elastic_resp_out = json.loads(f.read())
    with open("tests/cat/files/elastic_empty.json") as f:
        elastic_resp_empty = json.loads(f.read())
    with open("tests/cat/files/elastic_container_search.json") as f:
        elastic_resp_container_search = json.loads(f.read())
    with open("tests/cat/files/elastic_release_search.json") as f:
        elastic_resp_release_search = json.loads(f.read())
    with open("tests/cat/files/elastic_container_browse_no_params.json") as f:
        elastic_resp_container_browse_no_params = json.loads(f.read())

    return {
        "container_stats": ES_CONTAINER_STATS_RESP,
        "container_random": ES_CONTAINER_RANDOM_RESP,
        "container_search": elastic_resp_container_search,
        "container_browse_no_params": elastic_resp_container_browse_no_params,
        "release_search": elastic_resp_release_search,
        "release_refs_in": elastic_resp_in,
        "release_refs_out": elastic_resp_out,
        "release_refs_empty": elastic_resp_empty,
            }
