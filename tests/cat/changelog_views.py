import datetime
from dateutil.tz import tzutc

from fatcat_openapi_client.models.changelog_entry import ChangelogEntry
from fatcat_openapi_client.models.editgroup import Editgroup
from fatcat_openapi_client.models.editor import Editor

def test_changelog_view(client, fcclient):
    fcclient.get_changelog.return_value = [
            ChangelogEntry(index=6863689,
                           editgroup_id='lq5k5gnz4naitc7wj4rtz7xtqq',
                           timestamp=datetime.datetime(
                               2024, 5, 22, 23, 56, 23, 9854, tzinfo=tzutc()),
                           editgroup=Editgroup(
                               description="Dispatches from interzone",
                               )),
            ChangelogEntry(index=6863688,
                           editgroup_id='scmbogxw25evtcesfcab5qaboa',
                           timestamp=datetime.datetime(
                               2024, 5, 22, 23, 49, 32, 187881, tzinfo=tzutc()),
                           editgroup=Editgroup(
                               description="Files crawled from web using sandcrawler ingest tool",
                               )),

            ]
    rv = client.get("/cat/changelog")

    assert rv.status_code == 200
    assert "#6863689" in rv.text
    assert "#6863688" in rv.text
    assert "Files crawled from web using sandcrawler ingest tool" in rv.text
    assert "Dispatches from interzone" in rv.text

def test_changelog_entry_view(client, fcclient, entities):
    fcclient.get_changelog_entry.return_value = ChangelogEntry(
            index=6863689,
            editgroup_id='lq5k5gnz4naitc7wj4rtz7xtqq',
            timestamp=datetime.datetime(
                2024, 5, 22, 23, 56, 23, 9854, tzinfo=tzutc()),
            editgroup=Editgroup(
                description="Dispatches from interzone",
                ))
    fcclient.get_editor.return_value = Editor(username="vilmibm")
    fcclient.get_editgroup_annotations.return_value = []

    rv = client.get("/cat/changelog/6863689")

    print(rv.text)
    assert rv.status_code == 200
    assert "vilmibm" in rv.text
    assert "Dispatches from interzone" in rv.text
