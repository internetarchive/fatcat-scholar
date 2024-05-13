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

def test_malformed_entity(client, entity_types):
    for entity_type in entity_types:
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

def test_search_redirects(client):
    cases = [{"name": "blank redirect",
              "url": "/cat/search",
              "redirect_path": "/cat/release/search",
              "qarg": [],
              },
             {"name": "generic multi-term",
              "url": "/cat/search?q=foo%20bar",
              "redirect_path": "/cat/release/search",
              "qarg": ["q=foo%2Bbar", "generic=1"],},
             {"name": "doi",
              "url": "/cat/search?q=10.3390/arts8010040",
              "redirect_path": "/cat/release/lookup",
              "qarg": ["doi=10.3390%2Farts8010040"],},
             {"name":"pmcid",
              "url": "/cat/search?q=PMC5160550",
              "redirect_path": "/cat/release/lookup",
              "qarg": ["pmcid=PMC5160550"],},
             {"name": "issn",
              "url": "/cat/search?q=2333-2468",
              "redirect_path": "/cat/container/lookup",
              "qarg": ["issnl=2333-2468"],},
             {"name": "isbn13",
              "url": "/cat/search?q=978-0-12-415894-8",
              "redirect_path": "/cat/release/lookup",
              "qarg": ["isbn13=978-0-12-415894-8"], },
             {"name": "arxiv_id",
              "url": "/cat/search?q=0712.2293v1",
              "redirect_path": "/cat/release/lookup",
              "qarg": ["arxiv=0712.2293v1"], },
             {"name": "sha1",
              "url": "/cat/search?q=5bcf14bb375d294162c671b214da7771064d7ba7",
              "redirect_path": "/cat/file/lookup",
              "qarg": ["sha1=5bcf14bb375d294162c671b214da7771064d7ba7"], },
             {"name": "sha256",
              "url": "/cat/search?q=9f089668c7f604097ad250983ba27201b63272ea4b954c5f3e4e94d668e60cb4",
              "redirect_path": "/cat/file/lookup",
              "qarg": ["sha256=9f089668c7f604097ad250983ba27201b63272ea4b954c5f3e4e94d668e60cb4"], },
             {"name": "orcid",
              "url": "/cat/search?q=0000-0003-3118-6859",
              "redirect_path": "/cat/creator/lookup",
              "qarg": ["orcid=0000-0003-3118-6859"], },
             {"name": "generic single term",
              "url": "/cat/search?q=foobar",
              "redirect_path": "/cat/release/search",
              "qarg": ["q=foobar", "generic=1"],
              }
            ]

    for case in cases:
        rv = client.get(case["url"], follow_redirects=False)
        redirect_url = rv.headers.get("location")
        assert rv.status_code == 302, case["name"]
        assert case["redirect_path"] in redirect_url, case["name"]
        if len(case["qarg"]) > 0:
            for qarg in case["qarg"]:
                assert qarg in redirect_url, case["name"]
        else:
            assert "q=" not in redirect_url, case["name"]
            assert "generic=" not in redirect_url, case["name"]

def test_creator_lookup(client, fcclient, basic_entities):
    c = basic_entities["creator"]
    fcclient.lookup_creator.return_value = c

    for extidtype, extid in (("orcid", c.orcid), ("wikidata_qid", c.wikidata_qid)):
        rv = client.get(f"/cat/creator/lookup?{extidtype}={extid}", follow_redirects=False)
        assert f"cat/creator/{c.ident}" in rv.headers.get("location"), extidtype
        assert rv.status_code == 302, extidtype
        fcclient.lookup_creator.assert_called_with(**{extidtype: extid})

def test_release_lookup(client, fcclient, basic_entities):
    r = basic_entities["release"]
    fcclient.lookup_release.return_value = r
    # i left out some unused ext id types. we should probably drop them from
    # the codebase entirely (eg oai, mag)
    extidtypes = [("doi", r.ext_ids.doi), ("wikidata_qid", r.ext_ids.wikidata_qid),
                  ("pmid", r.ext_ids.pmid), ("pmcid", r.ext_ids.pmcid),
                  ("isbn13", r.ext_ids.isbn13), ("jstor", r.ext_ids.jstor),
                  ("arxiv", r.ext_ids.arxiv), ("ark", r.ext_ids.ark), ("hdl", r.ext_ids.hdl)]
    for extidtype, extid in extidtypes:
        rv = client.get(f"/cat/release/lookup?{extidtype}={extid}", follow_redirects=False)
        assert f"cat/release/{r.ident}" in rv.headers.get("location"), extidtype
        assert rv.status_code == 302, extidtype
        fcclient.lookup_release.assert_called_with(**{extidtype: extid})

def test_file_lookup(client, fcclient, basic_entities):
    f = basic_entities["file"]
    fcclient.lookup_file.return_value = f
    extidtypes = [("md5", f.md5), ("sha1", f.sha1), ("sha256", f.sha256)]
    for extidtype, extid in extidtypes:
        rv = client.get(f"/cat/file/lookup?{extidtype}={extid}", follow_redirects=False)
        assert f"cat/file/{f.ident}" in rv.headers.get("location"), extidtype
        assert rv.status_code == 302, extidtype
        fcclient.lookup_file.assert_called_with(**{extidtype: extid})

def test_container_lookup(client, fcclient, basic_entities):
    c = basic_entities["container"]
    fcclient.lookup_container.return_value = c
    extidtypes = [("issn", c.issnl), ("issne", c.issne), ("issnp", c.issnp),
                  ("issnl", c.issnl), ("wikidata_qid", c.wikidata_qid)]
    for extidtype, extid in extidtypes:
        rv = client.get(f"/cat/container/lookup?{extidtype}={extid}", follow_redirects=False)
        assert f"cat/container/{c.ident}" in rv.headers.get("location"), extidtype
        assert rv.status_code == 302, extidtype
        fcclient.lookup_container.assert_called_with(**{extidtype: extid})

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

def test_generic_entity_view_active_release(client, fcclient, mocker, basic_entities):
    r = basic_entities["release"]
    fcclient.get_release = mocker.MagicMock(return_value=r)
    res = client.get("/cat/release/abcdefghijklmnopqrstuvwxyz")
    assert res.status_code == 200
    assert r.title in res.text
    assert r.publisher in res.text

def test_generic_entity_view_deleted_release(client, fcclient, mocker, basic_entities):
    r = basic_entities["release"]
    r.state = "deleted"
    fcclient.get_release = mocker.MagicMock(return_value=r)
    res = client.get("/cat/release/abcdefghijklmnopqrstuvwxyz")
    assert res.status_code == 200
    assert "There used to be an entity here" in res.text

def test_generic_entity_view_redirect_release(client, fcclient, mocker, basic_entities):
    r = basic_entities["release"]
    r.state = "redirect"
    fcclient.get_release = mocker.MagicMock(return_value=r)
    res = client.get("/cat/release/abcdefghijklmnopqrstuvwxyz", follow_redirects=False)
    assert res.status_code == 302

def test_generic_entity_view_release_metadata(client, fcclient, basic_entities):
    r = basic_entities["release"]
    fcclient.get_release.return_value = r
    res = client.get("/cat/release/abcdefghijklmnopqrstuvwxyz/metadata", follow_redirects=False)
    assert res.status_code == 200
    assert r.pages in res.text
    assert r.volume in res.text

def test_generic_entity_view_container_view(client, fcclient, mocker, basic_entities):
    c = basic_entities["container"]
    fcclient.get_container.return_value = c
    # TODO use ES_CONTAINER_STATS_RESP
    es_m1 = mocker.patch("scholar.cat.web.get_elastic_container_stats", return_value={"total":0})
    es_m2 = mocker.patch("scholar.cat.web.get_elastic_container_random_releases")
    res = client.get("/cat/container/abcdefghijklmnopqrstuvwxyz")
    assert res.status_code == 200
    assert "urusei yatsura" in res.text
    es_m1.assert_called_once()
    es_m2.assert_called_once()

def test_generic_entity_view_container_view_coverage(client, fcclient, mocker, basic_entities):
    c = basic_entities["container"]

    fcclient.get_container.return_value = c
    m1 = mocker.patch("scholar.cat.web.get_elastic_container_stats", return_value={"total":0})
    m2 = mocker.patch("scholar.cat.web.get_elastic_preservation_by_type", return_value=[{}])

    res = client.get("/cat/container/abcdefghijklmnopqrstuvwxyz/coverage")

    assert res.status_code == 200
    assert "urusei yatsura" in res.text
    m1.assert_called_once()
    m2.assert_called_once()

def test_generic_entity_view_creator(client, fcclient, basic_entities):
    c = basic_entities["creator"]
    fcclient.get_creator.return_value = c

    res = client.get("/cat/creator/abcdefghijklmnopqrstuvwxyz")

    assert res.status_code == 200
    assert "tetsuo" in res.text
    assert "the iron man" in res.text

def test_generic_entity_view_file(client, fcclient, basic_entities):
    f = basic_entities["file"]
    fcclient.get_file.return_value = f

    res = client.get("/cat/file/abcdefghijklmnopqrstuvwxyz")
    assert res.status_code == 200
    assert f.md5 in res.text
    assert f.sha256 in res.text

def test_generic_entity_view_fileset(client, fcclient, basic_entities):
    fs = basic_entities["fileset"]
    fcclient.get_fileset.return_value = fs
    res = client.get("/cat/fileset/abcdefghijklmnopqrstuvwxyz")
    assert "File Manifest" in res.text
    assert res.status_code == 200
    assert fs.manifest[0].path in res.text

def test_generic_entity_view_webcapture(client, fcclient, basic_entities):
    wc = basic_entities["webcapture"]
    fcclient.get_webcapture.return_value = wc
    res = client.get("/cat/webcapture/abcdefghijklmnopqrstuvwxyz")
    assert res.status_code == 200
    assert wc.cdx[0].sha1 in res.text

def test_generic_entity_view_work(client, fcclient, basic_entities):
    w = basic_entities["work"]

    fcclient.get_work.return_value = w
    fcclient.get_work_releases.return_value = [basic_entities["release"]]
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
        mocker.patch("scholar.cat.web.generic_entity_view")
        client.get(case["route"])
        scholar.cat.web.generic_entity_view.assert_called_once()
        calls = scholar.cat.web.generic_entity_view.call_args[0]
        assert calls[2] == case["args"][0]
        assert calls[3] == case["args"][1]
        assert calls[4] == case["args"][2]
