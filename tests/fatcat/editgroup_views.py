import scholar.fatcat.web
import json
# TODO editgroup_view
# TODO editgroup_underscore_view
# TODO editgroup_diff_view

def test_generic_editgroup_entity_routes(client, mocker):
    editgroup_id = "x7jawh2rkncyxhm7jjy5geekoe"
    ident = "abcdefghijklmnopqrstuvwxyz"
    cases = [
            {"route": f"/fatcat/editgroup/{editgroup_id}/release/{ident}",
             "args": [editgroup_id, "release", ident, "release_view.html"]},
            {"route": f"/fatcat/editgroup/{editgroup_id}/release/{ident}/metadata",
             "args": [editgroup_id, "release", ident, "entity_view_metadata.html"]},
            {"route": f"/fatcat/editgroup/{editgroup_id}/release/{ident}/contribs",
             "args": [editgroup_id, "release", ident, "release_view_contribs.html"]},
            {"route": f"/fatcat/editgroup/{editgroup_id}/release/{ident}/references",
             "args": [editgroup_id, "release", ident, "release_view_references.html"]},

            {"route": f"/fatcat/editgroup/{editgroup_id}/work/{ident}",
             "args": [editgroup_id, "work", ident, "work_view.html"]},
            {"route": f"/fatcat/editgroup/{editgroup_id}/work/{ident}/metadata",
             "args": [editgroup_id, "work", ident, "entity_view_metadata.html"]},

            {"route": f"/fatcat/editgroup/{editgroup_id}/container/{ident}",
             "args": [editgroup_id, "container", ident, "container_view.html"]},
            {"route": f"/fatcat/editgroup/{editgroup_id}/container/{ident}/metadata",
             "args": [editgroup_id, "container", ident, "entity_view_metadata.html"]},

            {"route": f"/fatcat/editgroup/{editgroup_id}/creator/{ident}",
             "args": [editgroup_id, "creator", ident, "creator_view.html"]},
            {"route": f"/fatcat/editgroup/{editgroup_id}/creator/{ident}/metadata",
             "args": [editgroup_id, "creator", ident, "entity_view_metadata.html"]},

            {"route": f"/fatcat/editgroup/{editgroup_id}/file/{ident}",
             "args": [editgroup_id, "file", ident, "file_view.html"]},
            {"route": f"/fatcat/editgroup/{editgroup_id}/file/{ident}/metadata",
             "args": [editgroup_id, "file", ident, "entity_view_metadata.html"]},

            {"route": f"/fatcat/editgroup/{editgroup_id}/fileset/{ident}",
             "args": [editgroup_id, "fileset", ident, "fileset_view.html"]},
            {"route": f"/fatcat/editgroup/{editgroup_id}/fileset/{ident}/metadata",
             "args": [editgroup_id, "fileset", ident, "entity_view_metadata.html"]},

            {"route": f"/fatcat/editgroup/{editgroup_id}/webcapture/{ident}",
             "args": [editgroup_id, "webcapture", ident, "webcapture_view.html"]},
            {"route": f"/fatcat/editgroup/{editgroup_id}/webcapture/{ident}/metadata",
             "args": [editgroup_id, "webcapture", ident, "entity_view_metadata.html"]},
            ]

    for case in cases:
        mocker.patch("scholar.fatcat.web.generic_editgroup_entity_view")
        client.get(case["route"])
        scholar.fatcat.web.generic_editgroup_entity_view.assert_called_once()
        calls = scholar.fatcat.web.generic_editgroup_entity_view.call_args[0]
        assert calls[2] == case["args"][0], "editgroup id"
        assert calls[3] == case["args"][1], "entity type"
        assert calls[4] == case["args"][2], "entity id"
        assert calls[5] == case["args"][3], "template"

def test_generic_entity_editgroup_view_release(client, fcclient, mocker, entities, editgroup):
    r = entities["release"]
    ident = r.ident
    fcclient.get_editgroup.return_value = editgroup
    fcclient.get_release_revision.return_value = r
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/release/{ident}")
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert res.status_code == 200
    assert r.title in res.text
    assert r.publisher in res.text

def test_generic_entity_editgroup_view_release_contribs(client, fcclient, mocker, entities, editgroup):
    r = entities["release"]
    ident = r.ident
    fcclient.get_editgroup.return_value = editgroup
    fcclient.get_release_revision.return_value = r
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/release/{ident}/contribs")
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert res.status_code == 200
    assert "(the iron man, tetsuo)" in res.text

def test_generic_entity_editgroup_view_release_references(client, fcclient, mocker, entities, editgroup):
    r = entities["release"]
    ident = r.ident
    fcclient.get_editgroup.return_value = editgroup
    fcclient.get_release_revision.return_value = r
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/release/{ident}/references")
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert res.status_code == 200
    assert "References" in res.text

def test_generic_entity_editgroup_view_release_metadata(client, fcclient, mocker, entities, editgroup):
    r = entities["release"]
    ident = r.ident
    fcclient.get_editgroup.return_value = editgroup
    fcclient.get_release_revision.return_value = r
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/release/{ident}/metadata")
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert res.status_code == 200
    assert r.title in res.text
    assert r.publisher in res.text
    assert r.pages in res.text
    assert r.volume in res.text

def test_generic_entity_editgroup_view_container_view(client, fcclient, es, entities, es_resps, editgroup):
    c = entities["container"]
    ident = c.ident
    fcclient.get_container_revision.return_value = c
    fcclient.get_editgroup.return_value = editgroup
    es.side_effect = [
        (200, {}, json.dumps(es_resps["container_stats"])),
        (200, {}, json.dumps(es_resps["container_random"])),
    ]
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/container/{ident}")
    assert res.status_code == 200
    assert "urusei yatsura" in res.text
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text

def test_generic_entity_editgroup_view_container_view_metadata(client, fcclient, es, entities, es_resps, editgroup):
    c = entities["container"]
    ident = c.ident
    fcclient.get_container_revision.return_value = c
    fcclient.get_editgroup.return_value = editgroup
    es.side_effect = [
        (200, {}, json.dumps(es_resps["container_stats"])),
        (200, {}, json.dumps(es_resps["container_random"])),
    ]
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/container/{ident}/metadata")
    assert res.status_code == 200
    assert "urusei yatsura" in res.text
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text

def test_generic_entity_editgroup_view_creator_view(client, fcclient, es, entities, es_resps, editgroup):
    c = entities["creator"]
    ident = c.ident
    fcclient.get_creator_revision.return_value = c
    fcclient.get_editgroup.return_value = editgroup
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/creator/{ident}")
    assert res.status_code == 200
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert "tetsuo" in res.text
    assert "the iron man" in res.text

def test_generic_entity_editgroup_view_creator_view_metadata(client, fcclient, es, entities, es_resps, editgroup):
    c = entities["creator"]
    ident = c.ident
    fcclient.get_creator_revision.return_value = c
    fcclient.get_editgroup.return_value = editgroup
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/creator/{ident}/metadata")
    assert res.status_code == 200
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert "tetsuo" in res.text
    assert "the iron man" in res.text
    assert "wikidata_qid" in res.text
    assert "Q6251482" in res.text

def test_generic_entity_editgroup_view_file_view(client, fcclient, es, entities, es_resps, editgroup):
    f = entities["file"]
    ident = f.ident
    fcclient.get_file_revision.return_value = f
    fcclient.get_editgroup.return_value = editgroup
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/file/{ident}")
    assert res.status_code == 200
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert f.md5 in res.text
    assert f.sha256 in res.text

def test_generic_entity_editgroup_view_file_view_metadata(client, fcclient, es, entities, es_resps, editgroup):
    f = entities["file"]
    ident = f.ident
    fcclient.get_file_revision.return_value = f
    fcclient.get_editgroup.return_value = editgroup
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/file/{ident}/metadata")
    assert res.status_code == 200
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert f.md5 in res.text
    assert f.sha256 in res.text
    assert "release_ids" in res.text

def test_generic_entity_editgroup_view_fileset_view(client, fcclient, es, entities, es_resps, editgroup):
    f = entities["fileset"]
    ident = f.ident
    fcclient.get_fileset_revision.return_value = f
    fcclient.get_editgroup.return_value = editgroup
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/fileset/{ident}")
    assert res.status_code == 200
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert "File Manifest" in res.text
    assert res.status_code == 200
    assert f.manifest[0].path in res.text

def test_generic_entity_editgroup_view_fileset_view_metadata(client, fcclient, es, entities, es_resps, editgroup):
    f = entities["fileset"]
    ident = f.ident
    fcclient.get_fileset_revision.return_value = f
    fcclient.get_editgroup.return_value = editgroup
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/fileset/{ident}/metadata")
    assert res.status_code == 200
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert "File Manifest" not in res.text
    assert f.manifest[0].path in res.text

def test_generic_entity_editgroup_view_webcapture_view(client, fcclient, es, entities, es_resps, editgroup):
    w = entities["webcapture"]
    ident = w.ident
    fcclient.get_webcapture_revision.return_value = w
    fcclient.get_editgroup.return_value = editgroup
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/webcapture/{ident}")
    assert res.status_code == 200
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert w.cdx[0].sha1 in res.text

def test_generic_entity_editgroup_view_webcapture_view_metadata(client, fcclient, es, entities, es_resps, editgroup):
    w = entities["webcapture"]
    ident = w.ident
    fcclient.get_webcapture_revision.return_value = w
    fcclient.get_editgroup.return_value = editgroup
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/webcapture/{ident}/metadata")
    assert res.status_code == 200
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert w.cdx[0].sha1 in res.text
    assert "Entity Metadata" in res.text

def test_generic_entity_editgroup_view_work_view(client, fcclient, es, entities, es_resps, editgroup):
    w = entities["work"]
    ident = w.ident
    fcclient.get_work_revision.return_value = w
    fcclient.get_editgroup.return_value = editgroup
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/work/{ident}")
    assert res.status_code == 200
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert w.ident in res.text

def test_generic_entity_editgroup_view_work_view_metadata(client, fcclient, es, entities, es_resps, editgroup):
    w = entities["work"]
    ident = w.ident
    fcclient.get_work_revision.return_value = w
    fcclient.get_editgroup.return_value = editgroup
    res = client.get(f"/fatcat/editgroup/{editgroup.editgroup_id}/work/{ident}/metadata")
    assert res.status_code == 200
    assert f"as of editgroup_{editgroup.editgroup_id}" in res.text
    assert w.ident in res.text
    assert "Entity Metadata" in res.text
