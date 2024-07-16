import json

import scholar.cat.web

from uuid import UUID

# TODO /
# TODO /about
# TODO /stats
# TODO /release/search
# TODO /release/save
# TODO /coverage/search
# TODO /editgroup/{ident}
# TODO /editgroup/{ident}/diff
# TODO /editor routes
# TODO /u/{username}
# TODO common editgroup routes

def test_release_bibtex(client, fcclient, entities):
    r = entities["bigrelease"]
    fcclient.get_release.return_value = r

    rv = client.get(f"/cat/release/{r.ident}.bib")

    assert rv.status_code == 200
    assert rv.text == '''@article{faas_weckerly_2010, 
  title={Habitat Interference by Axis Deer on White-Tailed Deer}, 
  volume={74}, 
  ISSN={0022-541X}, 
  DOI={10.2193/2009-135}, 
  journal={Journal of Wildlife Management}, 
  publisher={Wiley (Blackwell Publishing)}, 
  author={Faas and Weckerly}, 
  year={2010}
  }''' # noqa W291

def test_release_citeproc(client, fcclient, entities):
    r = entities["bigrelease"]
    fcclient.get_release.return_value = r

    rv = client.get(f"/cat/release/{r.ident}/citeproc")

    assert rv.status_code == 200
    assert rv.text == "Faas and Weckerly (2010) ‘Habitat Interference by Axis Deer on White-Tailed Deer’, Journal of Wildlife Management, 74. doi: 10.2193/2009-135."

    rv = client.get(f"/cat/release/{r.ident}/citeproc?style=modern-language-association")

    assert rv.status_code == 200
    assert rv.text == "Faasand Weckerly. “Habitat Interference by Axis Deer on White-tailed Deer”. Journal of Wildlife Management, vol. 74, Wiley (Blackwell Publishing), 2010, doi:10.2193/2009-135."

    rv = client.get(f"/cat/release/{r.ident}/citeproc?style=csl-json")

    assert rv.status_code == 200
    assert rv.text == '{"type": "article-journal", "language": "en", "issued": {"date-parts": [[2010]]}, "DOI": "10.2193/2009-135", "ISSN": "0022-541X", "publisher": "Wiley (Blackwell Publishing)", "title": "Habitat Interference by Axis Deer on White-Tailed Deer", "volume": "74", "author": [{"family": "Faas"}, {"family": "Weckerly"}], "container-title": "Journal of Wildlife Management", "page-first": "698", "id": "unknown"}'

    rv = client.get(f"/cat/release/{r.ident}/citeproc?style=elsevier-harvard")

    assert rv.status_code == 200
    assert rv.text == "Faas, Weckerly, 2010. Habitat Interference by Axis Deer on White-Tailed Deer. Journal of Wildlife Management 74.. https://doi.org/10.2193/2009-135"

    rv = client.get(f"/cat/release/{r.ident}/citeproc?style=bad")

    assert rv.status_code == 400

def test_entity_history_views(client, fcclient, entities, histories):
    fcclient.get_release.return_value    = entities["release"]
    fcclient.get_file.return_value       = entities["file"]
    fcclient.get_fileset.return_value    = entities["fileset"]
    fcclient.get_container.return_value  = entities["container"]
    fcclient.get_webcapture.return_value = entities["webcapture"]
    fcclient.get_creator.return_value    = entities["creator"]
    fcclient.get_work.return_value       = entities["work"]

    fcclient.get_container_history.return_value  = histories["container"]
    fcclient.get_creator_history.return_value    = histories["creator"]
    fcclient.get_file_history.return_value       = histories["file"]
    fcclient.get_fileset_history.return_value    = histories["fileset"]
    fcclient.get_webcapture_history.return_value = histories["webcapture"]
    fcclient.get_release_history.return_value    = histories["release"]
    fcclient.get_work_history.return_value       = histories["work"]

    c = entities["container"]
    rv = client.get(f"/cat/container/{c.ident}/history")
    assert rv.status_code == 200
    assert "g4uijctf2nahznuvc2xxm5i5he" in rv.text
    assert "#4620617" in rv.text
    assert "2019-01-31" in rv.text

    cr = entities["creator"]
    rv = client.get(f"/cat/creator/{cr.ident}/history")
    assert rv.status_code == 200
    assert "#2796" in rv.text
    assert "ynn4nvuwafdtxiqboq7wzcarz4" in rv.text
    assert "orcid-bot" in rv.text

    f = entities["file"]
    rv = client.get(f"/cat/file/{f.ident}/history")
    assert rv.status_code == 200
    assert "#4873842" in rv.text
    assert "crawl-bot" in rv.text
    assert "bjiovs43zbf75pxze3udalm27a" in rv.text

    fs = entities["fileset"]
    rv = client.get(f"/cat/fileset/{fs.ident}/history")
    assert rv.status_code == 200
    assert "#2336005" in rv.text
    assert "bnewbold-archive" in rv.text
    assert "xl3rz6uxfrb2pgprzxictbkvxi" in rv.text

    wc = entities["webcapture"]
    rv = client.get(f"/cat/webcapture/{wc.ident}/history")
    assert rv.status_code == 200
    assert "#2336002" in rv.text
    assert "bnewbold-archive" in rv.text
    assert "kpuel5gcgjfrzkowokq54k633q" in rv.text

    r = entities["release"]
    rv = client.get(f"/cat/release/{r.ident}/history")
    assert rv.status_code == 200
    assert "#4529728" in rv.text
    assert "crossref-bot" in rv.text
    assert "h32n3zxlfvforca3oefqdxc3lm" in rv.text

    w = entities["work"]
    rv = client.get(f"/cat/work/{w.ident}/history")
    assert rv.status_code == 200
    assert "#4529728" in rv.text
    assert "crossref-bot" in rv.text
    assert "uggz4zervvgevn4gt7odo4ufnq" in rv.text

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

def test_creator_lookup(client, fcclient, entities):
    c = entities["creator"]
    fcclient.lookup_creator.return_value = c

    for extidtype, extid in (("orcid", c.orcid), ("wikidata_qid", c.wikidata_qid)):
        rv = client.get(f"/cat/creator/lookup?{extidtype}={extid}", follow_redirects=False)
        assert f"cat/creator/{c.ident}" in rv.headers.get("location"), extidtype
        assert rv.status_code == 302, extidtype
        fcclient.lookup_creator.assert_called_with(**{extidtype: extid})

def test_release_lookup(client, fcclient, entities):
    r = entities["release"]
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

def test_file_lookup(client, fcclient, entities):
    f = entities["file"]
    fcclient.lookup_file.return_value = f
    extidtypes = [("md5", f.md5), ("sha1", f.sha1), ("sha256", f.sha256)]
    for extidtype, extid in extidtypes:
        rv = client.get(f"/cat/file/lookup?{extidtype}={extid}", follow_redirects=False)
        assert f"cat/file/{f.ident}" in rv.headers.get("location"), extidtype
        assert rv.status_code == 302, extidtype
        fcclient.lookup_file.assert_called_with(**{extidtype: extid})

def test_container_lookup(client, fcclient, entities):
    c = entities["container"]
    fcclient.lookup_container.return_value = c
    extidtypes = [("issn", c.issnl), ("issne", c.issne), ("issnp", c.issnp),
                  ("issnl", c.issnl), ("wikidata_qid", c.wikidata_qid)]
    for extidtype, extid in extidtypes:
        rv = client.get(f"/cat/container/lookup?{extidtype}={extid}", follow_redirects=False)
        assert f"cat/container/{c.ident}" in rv.headers.get("location"), extidtype
        assert rv.status_code == 302, extidtype
        fcclient.lookup_container.assert_called_with(**{extidtype: extid})

def test_container_ident_browse(client, fcclient, es, es_resps, entities):
    c = entities["container"]
    c.state = "redirect"
    fcclient.get_container.return_value = c
    rv = client.get(f"/cat/container/{c.ident}/browse", follow_redirects=False)
    assert rv.status_code == 302

    c.state = "deleted"
    fcclient.get_container.return_value = c
    rv = client.get(f"/cat/container/{c.ident}/browse")
    assert rv.status_code == 200
    assert "There used to be an entity here" in rv.text

    c.state = "active"
    es.side_effect = [
        (200, {}, json.dumps(es_resps["container_browse_no_params"])),
        (200, {}, json.dumps(es_resps["release_search"])),
    ]
    rv = client.get(f"/cat/container/{c.ident}/browse")
    assert rv.status_code == 200

    rv = client.get(f"/cat/container/{c.ident}/browse?year=1969&issue=6&volume=13")
    assert rv.status_code == 200
    assert "Mourning" in rv.text
    assert "Volume 13, Issue 6 (1969)" in rv.text

def test_container_search(client, es, es_resps):
    rv = client.get("/cat/container/search")
    assert rv.status_code == 200
    assert "Journal/Conference Search" in rv.text

    es.side_effect = [
        (200, {}, json.dumps(es_resps["container_search"])),
    ]
    rv = client.get("/cat/container/search?q=tetsuo")
    assert rv.status_code == 200
    assert "out of 2 results" in rv.text
    assert "Herpetology" in rv.text

def test_container_ident_search(client, fcclient, es, es_resps, entities):
    c = entities["container"]
    fcclient.get_container.return_value = c

    rv = client.get(f"/cat/container/{c.ident}/search")
    assert rv.status_code == 200
    assert "Search inside Container" in rv.text

    es.side_effect = [
        (200, {}, json.dumps(es_resps["release_search"])),
    ]

    rv = client.get(f"/cat/container/{c.ident}/search?q=gecko")
    assert rv.status_code == 200
    assert "Mourning" in rv.text
    assert "out of 2 results" in rv.text

def test_generic_entity_view_active_release(client, fcclient, mocker, entities):
    r = entities["release"]
    fcclient.get_release = mocker.MagicMock(return_value=r)
    res = client.get("/cat/release/abcdefghijklmnopqrstuvwxyz")
    assert res.status_code == 200
    assert r.title in res.text
    assert r.publisher in res.text

def test_generic_entity_view_deleted_release(client, fcclient, mocker, entities):
    r = entities["release"]
    r.state = "deleted"
    fcclient.get_release = mocker.MagicMock(return_value=r)
    res = client.get("/cat/release/abcdefghijklmnopqrstuvwxyz")
    assert res.status_code == 200
    assert "There used to be an entity here" in res.text

def test_generic_entity_view_redirect_release(client, fcclient, mocker, entities):
    r = entities["release"]
    r.state = "redirect"
    fcclient.get_release = mocker.MagicMock(return_value=r)
    res = client.get("/cat/release/abcdefghijklmnopqrstuvwxyz", follow_redirects=False)
    assert res.status_code == 302

def test_generic_entity_view_webcapture_metadata(client, fcclient, entities):
    wc = entities["webcapture"]
    fcclient.get_webcapture.return_value = wc
    res = client.get("/cat/webcapture/abcdefghijklmnopqrstuvwxyz/metadata")
    assert res.status_code == 200
    assert wc.cdx[0].sha1 in res.text
    assert "content_scope" in res.text

def test_generic_entity_view_release_metadata(client, fcclient, entities):
    r = entities["release"]
    fcclient.get_release.return_value = r
    res = client.get("/cat/release/abcdefghijklmnopqrstuvwxyz/metadata", follow_redirects=False)
    assert res.status_code == 200
    assert r.pages in res.text
    assert r.volume in res.text

def test_generic_entity_view_release_contribs(client, fcclient, entities):
    r = entities["release"]
    fcclient.get_release.return_value = r
    res = client.get("/cat/release/abcdefghijklmnopqrstuvwxyz/contribs")
    assert res.status_code == 200
    assert "(the iron man, tetsuo)" in res.text

def test_generic_entity_view_container_view(client, fcclient, es, entities, es_resps):
    c = entities["container"]
    fcclient.get_container.return_value = c
    es.side_effect = [
        (200, {}, json.dumps(es_resps["container_stats"])),
        (200, {}, json.dumps(es_resps["container_random"])),
    ]
    res = client.get("/cat/container/abcdefghijklmnopqrstuvwxyz")
    assert res.status_code == 200
    assert "urusei yatsura" in res.text

def test_generic_entity_view_container_view_coverage(client, fcclient, mocker, entities):
    c = entities["container"]

    fcclient.get_container.return_value = c
    m1 = mocker.patch("scholar.cat.web.get_elastic_container_stats", return_value={"total":0})
    m2 = mocker.patch("scholar.cat.web.get_elastic_preservation_by_type", return_value=[{}])

    res = client.get("/cat/container/abcdefghijklmnopqrstuvwxyz/coverage")

    assert res.status_code == 200
    assert "urusei yatsura" in res.text
    m1.assert_called_once()
    m2.assert_called_once()

def test_generic_entity_view_creator(client, fcclient, entities):
    c = entities["creator"]
    fcclient.get_creator.return_value = c

    res = client.get("/cat/creator/abcdefghijklmnopqrstuvwxyz")

    assert res.status_code == 200
    assert "tetsuo" in res.text
    assert "the iron man" in res.text

def test_generic_entity_view_file(client, fcclient, entities):
    f = entities["file"]
    fcclient.get_file.return_value = f

    res = client.get("/cat/file/abcdefghijklmnopqrstuvwxyz")
    assert res.status_code == 200
    assert f.md5 in res.text
    assert f.sha256 in res.text

def test_generic_entity_view_fileset(client, fcclient, entities):
    fs = entities["fileset"]
    fcclient.get_fileset.return_value = fs
    res = client.get("/cat/fileset/abcdefghijklmnopqrstuvwxyz")
    assert "File Manifest" in res.text
    assert res.status_code == 200
    assert fs.manifest[0].path in res.text

def test_generic_entity_view_webcapture(client, fcclient, entities):
    wc = entities["webcapture"]
    fcclient.get_webcapture.return_value = wc
    res = client.get("/cat/webcapture/abcdefghijklmnopqrstuvwxyz")
    assert res.status_code == 200
    assert wc.cdx[0].sha1 in res.text

def test_generic_entity_view_work(client, fcclient, entities):
    w = entities["work"]
    fcclient.get_work.return_value = w
    fcclient.get_work_releases.return_value = [entities["release"]]
    res = client.get("/cat/work/abcdefghijklmnopqrstuvwxyz")
    assert res.status_code == 200
    assert entities["release"].title in res.text

def test_generic_entity_view_work_metadata(client, fcclient, entities):
    w = entities["work"]
    fcclient.get_work.return_value = w
    res = client.get("/cat/work/abcdefghijklmnopqrstuvwxyz/metadata")
    assert res.status_code == 200
    assert w.ident in res.text
    assert "Entity Metadata" in res.text

def test_generic_entity_view_fileset_metadata(client, fcclient, entities):
    fs = entities["fileset"]
    fcclient.get_fileset.return_value = fs
    res = client.get("/cat/fileset/abcdefghijklmnopqrstuvwxyz/metadata")
    assert res.status_code == 200
    assert fs.manifest[0].path in res.text

def test_generic_entity_view_file_metadata(client, fcclient, entities):
    f = entities["file"]
    fcclient.get_file.return_value = f
    res = client.get("/cat/file/abcdefghijklmnopqrstuvwxyz/metadata")
    assert res.status_code == 200
    assert f.md5 in res.text
    assert f.sha256 in res.text
    assert "release_ids" in res.text

def test_generic_entity_view_creator_metadata(client, fcclient, entities):
    c = entities["creator"]
    fcclient.get_creator.return_value = c

    res = client.get("/cat/creator/abcdefghijklmnopqrstuvwxyz/metadata")

    assert res.status_code == 200
    assert "tetsuo" in res.text
    assert "the iron man" in res.text
    assert "wikidata_qid" in res.text
    assert "Q6251482" in res.text

def test_generic_entity_view_container_view_metadata(client, fcclient, mocker, entities):
    c = entities["container"]
    fcclient.get_container.return_value = c
    res = client.get("/cat/container/abcdefghijklmnopqrstuvwxyz/metadata")
    assert res.status_code == 200
    assert "urusei yatsura" in res.text

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

def test_generic_entity_revision_views(client, mocker):
    cases = [{"route": "/cat/container/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d",
               "args": ["container", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "container_view.html"]},
             {"route": "/cat/container/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata",
               "args": ["container", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "entity_view_metadata.html"]},

             {"route": "/cat/creator/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d",
               "args": ["creator", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "creator_view.html"]},
             {"route": "/cat/creator/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata",
               "args": ["creator", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "entity_view_metadata.html"]},

             {"route": "/cat/file/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d",
               "args": ["file", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "file_view.html"]},
             {"route": "/cat/file/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata",
               "args": ["file", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "entity_view_metadata.html"]},

             {"route": "/cat/webcapture/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d",
               "args": ["webcapture", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "webcapture_view.html"]},
             {"route": "/cat/webcapture/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata",
               "args": ["webcapture", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "entity_view_metadata.html"]},

             {"route": "/cat/fileset/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d",
               "args": ["fileset", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "fileset_view.html"]},
             {"route": "/cat/fileset/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata",
               "args": ["fileset", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "entity_view_metadata.html"]},

             {"route": "/cat/work/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d",
               "args": ["work", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "work_view.html"]},
             {"route": "/cat/work/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata",
               "args": ["work", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "entity_view_metadata.html"]},

             {"route": "/cat/release/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d",
               "args": ["release", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "release_view.html"]},
             {"route": "/cat/release/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata",
               "args": ["release", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "entity_view_metadata.html"]},
             {"route": "/cat/release/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/contribs",
               "args": ["release", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "release_view_contribs.html"]},
             {"route": "/cat/release/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/references",
               "args": ["release", UUID("a078e5fe-0815-4ec4-82d8-7841b8a6317d"), "release_view_references.html"]},
            ]

    for case in cases:
        mocker.patch("scholar.cat.web.generic_entity_revision_view")
        client.get(case["route"])
        scholar.cat.web.generic_entity_revision_view.assert_called_once()
        calls = scholar.cat.web.generic_entity_revision_view.call_args[0]
        assert calls[2] == case["args"][0], "type"
        assert calls[3] == case["args"][1], "id"
        assert calls[4] == case["args"][2], "template"

def test_generic_entity_revision_view_release(client, fcclient, mocker, entities):
    r = entities["release"]
    fcclient.get_release_revision.return_value = r
    res = client.get("/cat/release/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d")
    assert res.status_code == 200
    assert r.title in res.text
    assert r.publisher in res.text

def test_generic_entity_revision_view_release_metadata(client, fcclient, entities):
    r = entities["release"]
    fcclient.get_release_revision.return_value = r
    res = client.get("/cat/release/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata")
    assert res.status_code == 200
    assert r.pages in res.text
    assert r.volume in res.text

def test_generic_entity_revision_view_container_view(client, fcclient, es, entities, es_resps):
    c = entities["container"]
    fcclient.get_container_revision.return_value = c
    es.side_effect = [
        (200, {}, json.dumps(es_resps["container_stats"])),
        (200, {}, json.dumps(es_resps["container_random"])),
    ]
    res = client.get("/cat/container/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d")
    assert res.status_code == 200
    assert "urusei yatsura" in res.text

def test_generic_entity_revision_view_container_view_metadata(client, fcclient, mocker, entities):
    c = entities["container"]
    fcclient.get_container_revision.return_value = c
    res = client.get("/cat/container/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata")
    assert res.status_code == 200
    assert "urusei yatsura" in res.text

def test_generic_entity_revision_view_creator(client, fcclient, entities):
    c = entities["creator"]
    fcclient.get_creator_revision.return_value = c

    res = client.get("/cat/creator/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d")

    assert res.status_code == 200
    assert "tetsuo" in res.text
    assert "the iron man" in res.text

def test_generic_entity_revision_view_creator_metadata(client, fcclient, entities):
    c = entities["creator"]
    fcclient.get_creator_revision.return_value = c

    res = client.get("/cat/creator/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata")

    assert res.status_code == 200
    assert "tetsuo" in res.text
    assert "the iron man" in res.text
    assert "wikidata_qid" in res.text
    assert "Q6251482" in res.text

def test_generic_entity_revision_view_file(client, fcclient, entities):
    f = entities["file"]
    fcclient.get_file_revision.return_value = f

    res = client.get("/cat/file/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d")
    assert res.status_code == 200
    assert f.md5 in res.text
    assert f.sha256 in res.text

def test_generic_entity_revision_view_file_metadata(client, fcclient, entities):
    f = entities["file"]
    fcclient.get_file_revision.return_value = f

    res = client.get("/cat/file/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata")
    assert res.status_code == 200
    assert f.md5 in res.text
    assert f.sha256 in res.text
    assert "release_ids" in res.text

def test_generic_entity_revision_view_fileset(client, fcclient, entities):
    fs = entities["fileset"]
    fcclient.get_fileset_revision.return_value = fs
    res = client.get("/cat/fileset/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d")
    assert "File Manifest" in res.text
    assert res.status_code == 200
    assert fs.manifest[0].path in res.text

def test_generic_entity_revision_view_fileset_metadata(client, fcclient, entities):
    fs = entities["fileset"]
    fcclient.get_fileset_revision.return_value = fs
    res = client.get("/cat/fileset/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata")
    assert res.status_code == 200
    assert fs.manifest[0].path in res.text

def test_generic_entity_revision_view_webcapture(client, fcclient, entities):
    wc = entities["webcapture"]
    fcclient.get_webcapture_revision.return_value = wc
    res = client.get("/cat/webcapture/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d")
    assert res.status_code == 200
    assert wc.cdx[0].sha1 in res.text

def test_generic_entity_revision_view_webcapture_metadata(client, fcclient, entities):
    wc = entities["webcapture"]
    fcclient.get_webcapture_revision.return_value = wc
    res = client.get("/cat/webcapture/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata")
    assert res.status_code == 200
    assert wc.cdx[0].sha1 in res.text

def test_generic_entity_revision_view_work(client, fcclient, entities):
    w = entities["work"]

    fcclient.get_work_revision.return_value = w
    #fcclient.get_work_releases.return_value = [entities["release"]]
    res = client.get("/cat/work/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d")
    assert res.status_code == 200
    assert w.ident in res.text

def test_generic_entity_revision_view_work_metadata(client, fcclient, entities):
    w = entities["work"]

    fcclient.get_work_revision.return_value = w
    res = client.get("/cat/work/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/metadata")
    assert res.status_code == 200
    assert w.ident in res.text
    assert "Entity Metadata" in res.text

def test_generic_entity_revision_view_release_contribs(client, fcclient, entities):
    r = entities["release"]

    fcclient.get_release_revision.return_value = r
    res = client.get("/cat/release/rev/a078e5fe-0815-4ec4-82d8-7841b8a6317d/contribs")
    assert res.status_code == 200
    assert "(the iron man, tetsuo)" in res.text
