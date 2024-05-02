import scholar.cat.web

import fatcat_openapi_client as fcapi

#import json

#from fixtures import *

#from fatcat_web.forms import ContainerEntityForm, FileEntityForm, ReleaseEntityForm

# TODO use in test below
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

ENTITY_TYPES = ["release", "work", "webcapture", "file", "fileset", "creator", "container"]


def test_malformed_entity(client):
    for entity_type in ENTITY_TYPES:
        rv = client.get("/cat/{}/9999999999".format(entity_type))
        assert rv.status_code == 422, f"malformed {entity_type}"
        # TODO what was up with this one; it's a valid ident, right?
        # I'm guessing it lives in the DB somewhere but I haven't tracked it down.
        #rv = client.get("/cat/{}/ccccccccccccccccccccccccca".format(entity_type))
        #assert rv.status_code == 404, "mystery {entity_type}"
        rv = client.get("/cat/{}/9999999999/history".format(entity_type))
        assert rv.status_code == 422, f"malformed {entity_type} history"
        rv = client.get("/cat/{}/f1f046a3-45c9-ffff-ffff-ffffffffffff".format(entity_type))
        assert rv.status_code == 422, f"malformed {entity_type} uuid"
        rv = client.get("/cat/{}/rev/f1f046a3-45c9-ffff-ffff-fffffffff".format(entity_type))
        assert rv.status_code == 422, "malformed {entity_type} rev"

#def test_lookups(app):
#
#    rv = app.get("/container/lookup")
#    assert rv.status_code == 200
#    rv = app.get("/container/lookup?issnl=9999-9999")
#    assert rv.status_code == 404
#    rv = app.get("/container/lookup?issnl=1234-5678")
#    assert rv.status_code == 302
#
#    rv = app.get("/creator/lookup")
#    assert rv.status_code == 200
#    rv = app.get("/creator/lookup?orcid=0000-0003-2088-7465")
#    assert rv.status_code == 302
#    rv = app.get("/creator/lookup?orcid=0000-0003-2088-0000")
#    assert rv.status_code == 404
#
#    rv = app.get("/file/lookup")
#    assert rv.status_code == 200
#    rv = app.get("/file/lookup?sha1=7d97e98f8af710c7e7fe703abc8f639e0ee507c4")
#    assert rv.status_code == 302
#    rv = app.get("/file/lookup?sha1=7d97e98f8af710c7e7f00000000000000ee507c4")
#    assert rv.status_code == 404
#
#    rv = app.get("/fileset/lookup")
#    assert rv.status_code == 404
#
#    rv = app.get("/webcapture/lookup")
#    assert rv.status_code == 404
#
#    rv = app.get("/release/lookup")
#    assert rv.status_code == 200
#    rv = app.get("/release/lookup?doi=10.123/abc")
#    assert rv.status_code == 302
#    rv = app.get("/release/lookup?doi=10.123%2Fabc")
#    assert rv.status_code == 302
#    rv = app.get("/release/lookup?doi=abcde")
#    assert rv.status_code == 400
#    rv = app.get("/release/lookup?doi=10.1234/uuu")
#    assert rv.status_code == 404
#
#    rv = app.get("/work/lookup")
#    assert rv.status_code == 404
#
#
#def test_web_container(app, mocker):
#
#    es_raw = mocker.patch("elasticsearch.connection.Urllib3HttpConnection.perform_request")
#    # these are basic ES stats for the container view pages
#    es_raw.side_effect = [
#        (200, {}, json.dumps(ES_CONTAINER_STATS_RESP)),
#        (200, {}, json.dumps(ES_CONTAINER_RANDOM_RESP)),
#    ]
#
#    rv = app.get("/container/aaaaaaaaaaaaaeiraaaaaaaaai")
#    assert rv.status_code == 200
#    rv = app.get("/container/aaaaaaaaaaaaaeiraaaaaaaaai/metadata")
#    assert rv.status_code == 200
#    rv = app.get("/container/aaaaaaaaaaaaaeiraaaaaaaaai/edit")
#    assert rv.status_code == 302
#    rv = app.get("/container/create")
#    assert rv.status_code == 302
#    rv = app.get("/container/rev/00000000-0000-0000-1111-fff000000002")
#    assert rv.status_code == 200
#    rv = app.get("/container/rev/00000000-0000-0000-1111-fff000000002/metadata")
#    assert rv.status_code == 200
#    rv = app.get("/editgroup/aaaaaaaaaaaabo53aaaaaaaaaq/container/aaaaaaaaaaaaaeiraaaaaaaaai")
#    assert rv.status_code == 200
#    rv = app.get(
#        "/editgroup/aaaaaaaaaaaabo53aaaaaaaaaq/container/aaaaaaaaaaaaaeiraaaaaaaaai/metadata"
#    )
#    assert rv.status_code == 200
#    rv = app.get(
#        "/editgroup/aaaaaaaaaaaabo53aaaaaaaaaq/container/aaaaaaaaaaaaaeiraaaaaaaaai/edit"
#    )
#    assert rv.status_code == 302
#
#
#def test_web_release(app):
#    # not logged in
#
#    rv = app.get("/release/aaaaaaaaaaaaarceaaaaaaaaai")
#    assert rv.status_code == 200
#    rv = app.get("/release/aaaaaaaaaaaaarceaaaaaaaaai/contribs")
#    assert rv.status_code == 200
#    rv = app.get("/release/aaaaaaaaaaaaarceaaaaaaaaai/references")
#    assert rv.status_code == 200
#    rv = app.get("/release/aaaaaaaaaaaaarceaaaaaaaaai/metadata")
#    assert rv.status_code == 200
#    rv = app.get("/release/rev/00000000-0000-0000-4444-fff000000002/contribs")
#    assert rv.status_code == 200
#    rv = app.get("/release/rev/00000000-0000-0000-4444-fff000000002/references")
#    assert rv.status_code == 200
#    rv = app.get("/release/rev/00000000-0000-0000-4444-fff000000002/metadata")
#    assert rv.status_code == 200
#    rv = app.get("/editgroup/aaaaaaaaaaaabo53aaaaaaaaaq/release/aaaaaaaaaaaaarceaaaaaaaaai")
#    assert rv.status_code == 200
#    rv = app.get(
#        "/editgroup/aaaaaaaaaaaabo53aaaaaaaaaq/release/aaaaaaaaaaaaarceaaaaaaaaai/contribs"
#    )
#    assert rv.status_code == 200
#    rv = app.get(
#        "/editgroup/aaaaaaaaaaaabo53aaaaaaaaaq/release/aaaaaaaaaaaaarceaaaaaaaaai/references"
#    )
#    assert rv.status_code == 200
#    rv = app.get(
#        "/editgroup/aaaaaaaaaaaabo53aaaaaaaaaq/release/aaaaaaaaaaaaarceaaaaaaaaai/metadata"
#    )
#    assert rv.status_code == 200
#
#    rv = app.get("/release/aaaaaaaaaaaaarceaaaaaaaaai/edit")
#    assert rv.status_code == 302
#    rv = app.get("/release/create")
#    assert rv.status_code == 302
#
#
#def test_web_search(app):
#
#    rv = app.get("/release/search")
#    assert rv.status_code == 200

def test_generic_entity_view_active_release(client, mocker, basic_entities):
    r = basic_entities["release"]

    mm = mocker.MagicMock()
    mm.get_release = mocker.MagicMock(return_value=r)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/release/abcdefghijklmnopqrstuvwxyz")

    assert res.status_code == 200
    assert r.title in res.text
    assert r.publisher in res.text

def test_generic_entity_view_deleted_release(client, mocker, basic_entities):
    r = basic_entities["release"]
    r.state = "deleted"

    mm = mocker.MagicMock()
    mm.get_release = mocker.MagicMock(return_value=r)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/release/abcdefghijklmnopqrstuvwxyz")

    assert res.status_code == 200
    assert "There used to be an entity here" in res.text

def test_generic_entity_view_redirect_release(client, mocker, basic_entities):
    r = basic_entities["release"]
    r.state = "redirect"

    mm = mocker.MagicMock()
    mm.get_release = mocker.MagicMock(return_value=r)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/release/abcdefghijklmnopqrstuvwxyz", follow_redirects=False)

    assert res.status_code == 302

def test_generic_entity_view_release_metadata(client, mocker, basic_entities):
    r = basic_entities["release"]
    mm = mocker.MagicMock()
    mm.get_release = mocker.MagicMock(return_value=r)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/release/abcdefghijklmnopqrstuvwxyz/metadata", follow_redirects=False)

    assert res.status_code == 200
    assert r.pages in res.text
    assert r.volume in res.text

def test_generic_entity_view_container_view(client, mocker, basic_entities):
    c = basic_entities["container"]

    mm = mocker.MagicMock()
    mm.get_container = mocker.MagicMock(return_value=c)
    # TODO use ES_CONTAINER_STATS_RESP
    m1 = mocker.patch("scholar.cat.web.get_elastic_container_stats", return_value={"total":0})
    m2 = mocker.patch("scholar.cat.web.get_elastic_container_random_releases")
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/container/abcdefghijklmnopqrstuvwxyz")

    assert res.status_code == 200
    assert "urusei yatsura" in res.text
    m1.assert_called_once()
    m2.assert_called_once()

def test_generic_entity_view_container_view_coverage(client, mocker, basic_entities):
    c = basic_entities["container"]

    mm = mocker.MagicMock()
    mm.get_container = mocker.MagicMock(return_value=c)
    m1 = mocker.patch("scholar.cat.web.get_elastic_container_stats", return_value={"total":0})
    m2 = mocker.patch("scholar.cat.web.get_elastic_preservation_by_type", return_value=[{}])
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/container/abcdefghijklmnopqrstuvwxyz/coverage")

    assert res.status_code == 200
    assert "urusei yatsura" in res.text
    m1.assert_called_once()
    m2.assert_called_once()

def test_generic_entity_view_creator(client, mocker, basic_entities):
    c = basic_entities["creator"]

    mm = mocker.MagicMock()
    mm.get_creator = mocker.MagicMock(return_value=c)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/creator/abcdefghijklmnopqrstuvwxyz")

    assert res.status_code == 200
    assert "tetsuo" in res.text
    assert "the iron man" in res.text

def test_generic_entity_view_file(client, mocker, basic_entities):
    f = basic_entities["file"]

    mm = mocker.MagicMock()
    mm.get_file = mocker.MagicMock(return_value=f)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/file/abcdefghijklmnopqrstuvwxyz")

    assert res.status_code == 200
    assert f.md5 in res.text
    assert f.sha256 in res.text

def test_generic_entity_view_fileset(client, mocker, basic_entities):
    fs = basic_entities["fileset"]

    mm = mocker.MagicMock()
    mm.get_fileset = mocker.MagicMock(return_value=fs)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/fileset/abcdefghijklmnopqrstuvwxyz")

    assert "File Manifest" in res.text
    assert res.status_code == 200
    assert fs.manifest[0].path in res.text

def test_generic_entity_view_webcapture(client, mocker, basic_entities):
    wc = basic_entities["webcapture"]

    mm = mocker.MagicMock()
    mm.get_webcapture = mocker.MagicMock(return_value=wc)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/webcapture/abcdefghijklmnopqrstuvwxyz")
    assert res.status_code == 200
    assert wc.cdx[0].sha1 in res.text

def test_generic_entity_view_work(client, mocker, basic_entities):
    w = basic_entities["work"]

    mm = mocker.MagicMock()
    mm.get_work = mocker.MagicMock(return_value=w)
    mm.get_work_releases = mocker.MagicMock(return_value=[basic_entities["release"]])
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/work/abcdefghijklmnopqrstuvwxyz")
    assert res.status_code == 200
    assert basic_entities["release"].title in res.text

def test_generic_entity_views(client, mocker):
    cases = [{"route": "/cat/container/abcdefghijklmnopqrstuvwxyz/coverage",
               "args": ["container", "abcdefghijklmnopqrstuvwxyz", "container_view_coverage.html"]},
             {"route": "/cat/container_abcdefghijklmnopqrstuvwxyz",
               "args": ["container", "abcdefghijklmnopqrstuvwxyz", "container_view.html"]},
             {"route": "/cat/container/abcdefghijklmnopqrstuvwxyz",
               "args": ["container", "abcdefghijklmnopqrstuvwxyz", "container_view.html"]},
             {"route": "/cat/container/abcdefghijklmnopqrstuvwxyz/metadata",
               "args": ["container", "abcdefghijklmnopqrstuvwxyz", "entity_view_metadata.html"]},

             {"route": "/cat/file_abcdefghijklmnopqrstuvwxyz",
               "args": ["file", "abcdefghijklmnopqrstuvwxyz", "file_view.html"]},
             {"route": "/cat/file/abcdefghijklmnopqrstuvwxyz",
               "args": ["file", "abcdefghijklmnopqrstuvwxyz", "file_view.html"]},
             {"route": "/cat/file/abcdefghijklmnopqrstuvwxyz/metadata",
               "args": ["file", "abcdefghijklmnopqrstuvwxyz", "entity_view_metadata.html"]},

             {"route": "/cat/fileset_abcdefghijklmnopqrstuvwxyz",
               "args": ["fileset", "abcdefghijklmnopqrstuvwxyz", "fileset_view.html"]},
             {"route": "/cat/fileset/abcdefghijklmnopqrstuvwxyz",
               "args": ["fileset", "abcdefghijklmnopqrstuvwxyz", "fileset_view.html"]},
             {"route": "/cat/fileset/abcdefghijklmnopqrstuvwxyz/metadata",
               "args": ["fileset", "abcdefghijklmnopqrstuvwxyz", "entity_view_metadata.html"]},

             {"route": "/cat/creator/abcdefghijklmnopqrstuvwxyz",
               "args": ["creator", "abcdefghijklmnopqrstuvwxyz", "creator_view.html"]},
             {"route": "/cat/creator_abcdefghijklmnopqrstuvwxyz",
               "args": ["creator", "abcdefghijklmnopqrstuvwxyz", "creator_view.html"]},
             {"route": "/cat/creator/abcdefghijklmnopqrstuvwxyz/metadata",
               "args": ["creator", "abcdefghijklmnopqrstuvwxyz", "entity_view_metadata.html"]},

             {"route": "/cat/release_abcdefghijklmnopqrstuvwxyz",
               "args": ["release", "abcdefghijklmnopqrstuvwxyz", "release_view.html"]},
             {"route": "/cat/release/abcdefghijklmnopqrstuvwxyz",
               "args": ["release", "abcdefghijklmnopqrstuvwxyz", "release_view.html"]},
             {"route": "/cat/release/abcdefghijklmnopqrstuvwxyz/contribs",
               "args": ["release", "abcdefghijklmnopqrstuvwxyz", "release_view_contribs.html"]},
             {"route": "/cat/release/abcdefghijklmnopqrstuvwxyz/references",
               "args": ["release", "abcdefghijklmnopqrstuvwxyz", "release_view_references.html"]},
             {"route": "/cat/release/abcdefghijklmnopqrstuvwxyz/metadata",
               "args": ["release", "abcdefghijklmnopqrstuvwxyz", "entity_view_metadata.html"]},

             {"route": "/cat/webcapture/abcdefghijklmnopqrstuvwxyz",
               "args": ["webcapture", "abcdefghijklmnopqrstuvwxyz", "webcapture_view.html"]},
             {"route": "/cat/webcapture_abcdefghijklmnopqrstuvwxyz",
               "args": ["webcapture", "abcdefghijklmnopqrstuvwxyz", "webcapture_view.html"]},
             {"route": "/cat/webcapture/abcdefghijklmnopqrstuvwxyz/metadata",
               "args": ["webcapture", "abcdefghijklmnopqrstuvwxyz", "entity_view_metadata.html"]},

             {"route": "/cat/work/abcdefghijklmnopqrstuvwxyz/metadata",
               "args": ["work", "abcdefghijklmnopqrstuvwxyz", "entity_view_metadata.html"]},
             {"route": "/cat/work_abcdefghijklmnopqrstuvwxyz",
               "args": ["work", "abcdefghijklmnopqrstuvwxyz", "work_view.html"]},
             {"route": "/cat/work/abcdefghijklmnopqrstuvwxyz",
               "args": ["work", "abcdefghijklmnopqrstuvwxyz", "work_view.html"]},
            ]

    for case in cases:
        with mocker.patch("scholar.cat.web.generic_entity_view"):
            client.get(case["route"])
            scholar.cat.web.generic_entity_view.assert_called_once()
            calls = scholar.cat.web.generic_entity_view.call_args[0]
            assert calls[2] == case["args"][0]
            assert calls[3] == case["args"][1]
            assert calls[4] == case["args"][2]
