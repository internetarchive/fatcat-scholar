import scholar.cat.web

import fatcat_openapi_client as fcapi

#import json

#from fixtures import *

#from fatcat_web.forms import ContainerEntityForm, FileEntityForm, ReleaseEntityForm

#DUMMY_DEMO_ENTITIES = {
#    "container": ("aaaaaaaaaaaaaeiraaaaaaaaai", "00000000-0000-0000-1111-fff000000002"),
#    # note inconsistency here (q not i)
#    "creator": ("aaaaaaaaaaaaaircaaaaaaaaaq", "00000000-0000-0000-2222-fff000000002"),
#    "file": ("aaaaaaaaaaaaamztaaaaaaaaai", "00000000-0000-0000-3333-fff000000002"),
#    "fileset": ("aaaaaaaaaaaaaztgaaaaaaaaai", "00000000-0000-0000-6666-fff000000002"),
#    "webcapture": ("aaaaaaaaaaaaa53xaaaaaaaaai", "00000000-0000-0000-7777-fff000000002"),
#    "release": ("aaaaaaaaaaaaarceaaaaaaaaai", "00000000-0000-0000-4444-fff000000002"),
#    "work": ("aaaaaaaaaaaaavkvaaaaaaaaai", "00000000-0000-0000-5555-fff000000002"),
#}
#
#REALISTIC_DEMO_ENTITIES = {
#    "container": "aaaaaaaaaaaaaeiraaaaaaaaam",
#    "creator": "aaaaaaaaaaaaaircaaaaaaaaam",
#    "file": "aaaaaaaaaaaaamztaaaaaaaaam",
#    "fileset": "aaaaaaaaaaaaaztgaaaaaaaaam",
#    "webcapture": "aaaaaaaaaaaaa53xaaaaaaaaam",
#    "release": "aaaaaaaaaaaaarceaaaaaaaaam",
#    "work": "aaaaaaaaaaaaavkvaaaaaaaaam",
#}
#
#
#def test_entity_basics(app, mocker):
#
#    es_raw = mocker.patch("elasticsearch.connection.Urllib3HttpConnection.perform_request")
#    # these are basic ES stats for the container view pages
#    es_raw.side_effect = [
#        (200, {}, json.dumps(ES_CONTAINER_STATS_RESP)),
#        (200, {}, json.dumps(ES_CONTAINER_RANDOM_RESP)),
#    ]
#
#    for entity_type, (ident, revision) in DUMMY_DEMO_ENTITIES.items():
#        # good requests
#        rv = app.get("/{}/{}".format(entity_type, ident))
#        assert rv.status_code == 200
#        rv = app.get("/{}_{}".format(entity_type, ident))
#        assert rv.status_code == 302
#        rv = app.get("/{}/{}/history".format(entity_type, ident))
#        assert rv.status_code == 200
#        rv = app.get("/{}/{}/metadata".format(entity_type, ident))
#        assert rv.status_code == 200
#        rv = app.get("/{}/rev/{}".format(entity_type, revision))
#        assert rv.status_code == 200
#        rv = app.get("/{}/rev/{}_something".format(entity_type, revision))
#        assert rv.status_code == 404
#        rv = app.get("/{}/rev/{}/metadata".format(entity_type, revision))
#        assert rv.status_code == 200
#        print("/editgroup/aaaaaaaaaaaabo53aaaaaaaaaq/{}/{}".format(entity_type, ident))
#        rv = app.get("/editgroup/aaaaaaaaaaaabo53aaaaaaaaaq/{}/{}".format(entity_type, ident))
#        assert rv.status_code == 200
#        rv = app.get(
#            "/editgroup/aaaaaaaaaaaabo53aaaaaaaaaq/{}/{}/metadata".format(entity_type, ident)
#        )
#        assert rv.status_code == 200
#
#        # bad requests
#        rv = app.get("/{}/9999999999".format(entity_type))
#        assert rv.status_code == 404
#        rv = app.get("/{}/9999999999/history".format(entity_type))
#        assert rv.status_code == 404
#        rv = app.get("/{}/f1f046a3-45c9-ffff-ffff-ffffffffffff".format(entity_type))
#        assert rv.status_code == 404
#        rv = app.get("/{}/rev/f1f046a3-45c9-ffff-ffff-fffffffff".format(entity_type))
#        assert rv.status_code == 404
#        rv = app.get("/{}/ccccccccccccccccccccccccca".format(entity_type))
#        assert rv.status_code == 404
#
#        # TODO: redirects and deleted entities
#
#
#def test_web_deleted_release(app, api):
#    # specific regression test for view of a deleted release
#
#    # create release
#    eg = quick_eg(api)
#    r1 = ReleaseEntity(
#        title="some title",
#        ext_ids=ReleaseExtIds(),
#    )
#    r1edit = api.create_release(eg.editgroup_id, r1)
#    api.accept_editgroup(eg.editgroup_id)
#
#    # delete
#    eg = quick_eg(api)
#    api.delete_release(eg.editgroup_id, r1edit.ident)
#    api.accept_editgroup(eg.editgroup_id)
#    r2 = api.get_release(r1edit.ident)
#    assert r2.state == "deleted"
#
#    rv = app.get("/release/{}".format(r2.ident))
#    assert rv.status_code == 200
#    rv = app.get("/release/{}/metadata".format(r2.ident))
#    assert rv.status_code == 200
#    rv = app.get("/release/{}/history".format(r2.ident))
#    assert rv.status_code == 200
#
#
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
#def test_web_file(app):
#    # not logged in
#
#    rv = app.get("/file/aaaaaaaaaaaaamztaaaaaaaaai")
#    assert rv.status_code == 200
#    rv = app.get("/file/aaaaaaaaaaaaamztaaaaaaaaai/edit")
#    assert rv.status_code == 302
#    rv = app.get("/file/create")
#    assert rv.status_code == 302
#
#
#def test_web_fileset(app):
#    # not logged in
#
#    rv = app.get("/fileset/aaaaaaaaaaaaaztgaaaaaaaaai")
#    assert rv.status_code == 200
#    rv = app.get("/fileset/aaaaaaaaaaaaaztgaaaaaaaaai/edit")
#    assert rv.status_code == 302
#    rv = app.get("/fileset/create")
#    assert rv.status_code == 302
#
#
#def test_web_webcatpure(app):
#    # not logged in
#
#    rv = app.get("/webcapture/aaaaaaaaaaaaa53xaaaaaaaaai")
#    assert rv.status_code == 200
#    rv = app.get("/webcapture/aaaaaaaaaaaaa53xaaaaaaaaai/edit")
#    assert rv.status_code == 302
#    rv = app.get("/webcapture/create")
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

#def test_web_work(client):
#    rv = client.get("/work/aaaaaaaaaaaaavkvaaaaaaaaai")
#    assert rv.status_code == 200

def test_generic_entity_view_active_release(client, mocker, basic_entities):
    r = basic_entities["release"]

    mm = mocker.MagicMock()
    mm.get_release = mocker.MagicMock(return_value=r)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/release/abc")

    assert res.status_code == 200
    assert r.title in res.text
    assert r.publisher in res.text

def test_generic_entity_view_deleted_release(client, mocker, basic_entities):
    r = basic_entities["release"]
    r.state = "deleted"

    mm = mocker.MagicMock()
    mm.get_release = mocker.MagicMock(return_value=r)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/release/abc")

    assert res.status_code == 200
    assert "There used to be an entity here" in res.text

def test_generic_entity_view_redirect_release(client, mocker, basic_entities):
    r = basic_entities["release"]
    r.state = "redirect"

    mm = mocker.MagicMock()
    mm.get_release = mocker.MagicMock(return_value=r)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/release/abc", follow_redirects=False)

    assert res.status_code == 302

def test_generic_entity_view_release_metadata(client, mocker, basic_entities):
    r = basic_entities["release"]
    mm = mocker.MagicMock()
    mm.get_release = mocker.MagicMock(return_value=r)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/release/metadata", follow_redirects=False)

    assert res.status_code == 200
    assert r.pages in res.text
    assert r.volume in res.text

def test_generic_entity_view_container_view(client, mocker, basic_entities):
    c = basic_entities["container"]

    mm = mocker.MagicMock()
    mm.get_container = mocker.MagicMock(return_value=c)
    m1 = mocker.patch("scholar.cat.web.get_elastic_container_stats", return_value={"total":0})
    m2 = mocker.patch("scholar.cat.web.get_elastic_container_random_releases")
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/container/abc")

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

    res = client.get("/cat/container/abc/coverage")

    assert res.status_code == 200
    assert "urusei yatsura" in res.text
    m1.assert_called_once()
    m2.assert_called_once()

def test_generic_entity_view_creator(client, mocker, basic_entities):
    c = basic_entities["creator"]

    mm = mocker.MagicMock()
    mm.get_creator = mocker.MagicMock(return_value=c)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/creator/abc")

    assert res.status_code == 200
    assert "tetsuo" in res.text
    assert "the iron man" in res.text

def test_generic_entity_view_file(client, mocker, basic_entities):
    f = basic_entities["file"]

    mm = mocker.MagicMock()
    mm.get_file = mocker.MagicMock(return_value=f)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/file/abc")

    assert res.status_code == 200
    assert f.md5 in res.text
    assert f.sha256 in res.text

def test_generic_entity_view_fileset(client, mocker, basic_entities):
    fs = basic_entities["fileset"]

    mm = mocker.MagicMock()
    mm.get_fileset = mocker.MagicMock(return_value=fs)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/fileset/abc")

    assert "File Manifest" in res.text
    assert res.status_code == 200
    assert fs.manifest[0].path in res.text

def test_generic_entity_view_webcapture(client, mocker, basic_entities):
    wc = basic_entities["webcapture"]

    mm = mocker.MagicMock()
    mm.get_webcapture = mocker.MagicMock(return_value=wc)
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/webcapture/abc")
    assert res.status_code == 200
    assert wc.cdx[0].sha1 in res.text

def test_generic_entity_view_work(client, mocker, basic_entities):
    w = basic_entities["work"]

    mm = mocker.MagicMock()
    mm.get_work = mocker.MagicMock(return_value=w)
    mm.get_work_releases = mocker.MagicMock(return_value=[basic_entities["release"]])
    m = mocker.patch("scholar.cat.web.DefaultApi", return_value=mm)

    res = client.get("/cat/work/abc")
    assert res.status_code == 200
    assert basic_entities["release"].title in res.text

def test_generic_entity_views(client, mocker):
    cases = [{"route": "/cat/container/abc/coverage",
               "args": ["container", "abc", "container_view_coverage.html"]},
             {"route": "/cat/container_abc",
               "args": ["container", "abc", "container_view.html"]},
             {"route": "/cat/container/abc",
               "args": ["container", "abc", "container_view.html"]},
             {"route": "/cat/container/abc/metadata",
               "args": ["container", "abc", "entity_view_metadata.html"]},

             {"route": "/cat/file_abc",
               "args": ["file", "abc", "file_view.html"]},
             {"route": "/cat/file/abc",
               "args": ["file", "abc", "file_view.html"]},
             {"route": "/cat/file/abc/metadata",
               "args": ["file", "abc", "entity_view_metadata.html"]},

             {"route": "/cat/fileset_abc",
               "args": ["fileset", "abc", "fileset_view.html"]},
             {"route": "/cat/fileset/abc",
               "args": ["fileset", "abc", "fileset_view.html"]},
             {"route": "/cat/fileset/abc/metadata",
               "args": ["fileset", "abc", "entity_view_metadata.html"]},

             {"route": "/cat/creator/abc",
               "args": ["creator", "abc", "creator_view.html"]},
             {"route": "/cat/creator_abc",
               "args": ["creator", "abc", "creator_view.html"]},
             {"route": "/cat/creator/abc/metadata",
               "args": ["creator", "abc", "entity_view_metadata.html"]},

             {"route": "/cat/release_abc",
               "args": ["release", "abc", "release_view.html"]},
             {"route": "/cat/release/abc",
               "args": ["release", "abc", "release_view.html"]},
             {"route": "/cat/release/abc/contribs",
               "args": ["release", "abc", "release_view_contribs.html"]},
             {"route": "/cat/release/abc/references",
               "args": ["release", "abc", "release_view_references.html"]},
             {"route": "/cat/release/abc/metadata",
               "args": ["release", "abc", "entity_view_metadata.html"]},

             {"route": "/cat/webcapture/abc",
               "args": ["webcapture", "abc", "webcapture_view.html"]},
             {"route": "/cat/webcapture_abc",
               "args": ["webcapture", "abc", "webcapture_view.html"]},
             {"route": "/cat/webcapture/abc/metadata",
               "args": ["webcapture", "abc", "entity_view_metadata.html"]},

             {"route": "/cat/work/abc/metadata",
               "args": ["work", "abc", "entity_view_metadata.html"]},
             {"route": "/cat/work_abc",
               "args": ["work", "abc", "work_view.html"]},
             {"route": "/cat/work/abc",
               "args": ["work", "abc", "work_view.html"]},
            ]

    for case in cases:
        with mocker.patch("scholar.cat.web.generic_entity_view"):
            client.get(case["route"])
            scholar.cat.web.generic_entity_view.assert_called_once()
            calls = scholar.cat.web.generic_entity_view.call_args[0]
            assert calls[2] == case["args"][0]
            assert calls[3] == case["args"][1]
            assert calls[4] == case["args"][2]
