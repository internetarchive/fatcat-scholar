import datetime
from dateutil.tz import tzutc
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
    mocker.patch("scholar.depends.DefaultApi", return_value=mm)
    return mm

@pytest.fixture
def es(mocker):
    return mocker.patch("elasticsearch.connection.Urllib3HttpConnection.perform_request")

@pytest.fixture
def entities():
    return {
        # TODO this is the citation i'm getting out. i'd like this to look more
        # real. should grab the dump of a release entity with a better citation
        # output and pull in more properties.
        # the iron man...038/35036653.
        "bigrelease": EG_RELEASE,
        "release": fcapi.ReleaseEntity(
            revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
            state="active",
            title="steel and lace",
            release_stage="published",
            release_year="1990",
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
            contribs=[
                fcapi.ReleaseContrib(
                    creator=fcapi.CreatorEntity(
                        display_name="tetsuo the iron man",
                        given_name="tetsuo",
                        ident="iimvc523xbhqlav6j3sbthuehu",
                        orcid="0000-0003-3118-6859",
                        revision="52444283-850c-41d5-945b-bd7c6112cb89",
                        state="active",
                        wikidata_qid="Q6251482",
                        surname="the iron man"),
                    ),
                fcapi.ReleaseContrib(
                    creator=fcapi.CreatorEntity(
                        display_name="ileana del socorro vazquez carrillo",
                        given_name="ileana",
                        ident="cad2oi3x3fdwdkv2cwvtaebye4",
                        orcid="0000-0002-7600-7319",
                        revision="502d5f6a-f455-4f48-88b4-812c008ca72b",
                        state="active",
                        surname="del socorro vazquez carrillo"),
                    ),
            ],
            abstracts=[]),
        "container": fcapi.ContainerEntity(
            revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
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
            revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
            state="active",
            wikidata_qid="Q6251482",
            surname="the iron man"),
        "file": fcapi.FileEntity(
            ident="y6k6estkpbdrpmdjcw2cbjvpmu",
            revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
            size=66,
            md5="f013d66c7f6817d08b7eb2a93e6d0440",
            sha1="3d0755107a3fc2b81d0a3886477b5000747512fd",
            sha256="a77e4c11a57f1d757fca5754a8f83b5d4ece49a2d28596889127c1a2f3f28832",
            release_ids=[],
            releases=[],
            ),
        "fileset": fcapi.FilesetEntity(
            ident="ho376wmdanckpp66iwfs7g22ne",
            revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
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
            revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
            ident="z7uaeatyvfgwdpuxtrdu4okqii",
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
            revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
            ident="uggz4zervvgevn4gt7odo4ufnq",
            state="active",
            ),
    }

@pytest.fixture
def es_resps():
    with open("tests/fatcat/files/elastic_refs_in_release.json") as f:
        elastic_resp_in = json.loads(f.read())
    with open("tests/fatcat/files/elastic_refs_out_release.json") as f:
        elastic_resp_out = json.loads(f.read())
    with open("tests/fatcat/files/elastic_empty.json") as f:
        elastic_resp_empty = json.loads(f.read())
    with open("tests/fatcat/files/elastic_container_search.json") as f:
        elastic_resp_container_search = json.loads(f.read())
    with open("tests/fatcat/files/elastic_release_search.json") as f:
        elastic_resp_release_search = json.loads(f.read())
    with open("tests/fatcat/files/elastic_container_browse_no_params.json") as f:
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

@pytest.fixture
def histories():
    return {"container": CONTAINER_HISTORY,
            "creator": CREATOR_HISTORY,
            "file": FILE_HISTORY,
            "fileset": FILESET_HISTORY,
            "webcapture": WEBCAPTURE_HISTORY,
            "release": RELEASE_HISTORY,
            "work": WORK_HISTORY,
            }

CONTAINER_HISTORY = [{'changelog_entry': {'editgroup': None,
                     'editgroup_id': 'g4uijctf2nahznuvc2xxm5i5he',
                     'index': 5638366,
                     'timestamp': datetime.datetime(2021, 12, 1, 1, 23, 57, 289497, tzinfo=tzutc())},
 'edit': {'edit_id': '1a080f79-ffe3-4174-87bc-10ea615533e2',
          'editgroup_id': 'g4uijctf2nahznuvc2xxm5i5he',
          'extra': None,
          'ident': 'bi7rkf2w6jc5fd6z2szjd4k7j4',
          'prev_revision': 'f89ccd2e-a761-4b41-ba2d-313bfb42c7b7',
          'redirect_ident': None,
          'revision': '198c87e7-9124-4371-b34a-cb5e75bbb77c'},
 'editgroup': {'annotations': None,
               'changelog_index': 5638366,
               'created': datetime.datetime(2021, 12, 1, 1, 23, 56, 744205, tzinfo=tzutc()),
               'description': 'Automated import of container-level metadata '
                              'from Chocula tool.',
               'editgroup_id': 'g4uijctf2nahznuvc2xxm5i5he',
               'editor': {'editor_id': '4ravvsiw3rbypj2ltuugvtw6nu',
                          'is_active': True,
                          'is_admin': True,
                          'is_bot': True,
                          'username': 'journal-metadata-bot'},
               'editor_id': '4ravvsiw3rbypj2ltuugvtw6nu',
               'edits': None,
               'extra': {'agent': 'fatcat_tools.ChoculaImporter',
                         'git_rev': 'v0.5.0-50-gb1efd59'},
               'submitted': None}}, {'changelog_entry': {'editgroup': None,
                     'editgroup_id': 'bcdzkoafrvgetpxpraxhidzf2u',
                     'index': 4620617,
                     'timestamp': datetime.datetime(2020, 8, 5, 18, 46, 55, 844170, tzinfo=tzutc())},
 'edit': {'edit_id': '4aeccb9e-7722-4883-8281-ade416006f68',
          'editgroup_id': 'bcdzkoafrvgetpxpraxhidzf2u',
          'extra': None,
          'ident': 'bi7rkf2w6jc5fd6z2szjd4k7j4',
          'prev_revision': 'e4d6f182-1de6-4ea6-a44d-42ef3744a239',
          'redirect_ident': None,
          'revision': 'f89ccd2e-a761-4b41-ba2d-313bfb42c7b7'},
 'editgroup': {'annotations': None,
               'changelog_index': 4620617,
               'created': datetime.datetime(2020, 8, 5, 18, 46, 55, 489524, tzinfo=tzutc()),
               'description': 'Automated import of container-level metadata '
                              'from Chocula tool.',
               'editgroup_id': 'bcdzkoafrvgetpxpraxhidzf2u',
               'editor': {'editor_id': '4ravvsiw3rbypj2ltuugvtw6nu',
                          'is_active': True,
                          'is_admin': True,
                          'is_bot': True,
                          'username': 'journal-metadata-bot'},
               'editor_id': '4ravvsiw3rbypj2ltuugvtw6nu',
               'edits': None,
               'extra': {'agent': 'fatcat_tools.ChoculaImporter',
                         'git_rev': 'v0.3.2-195-g4f80b87'},
               'submitted': None}}, {'changelog_entry': {'editgroup': None,
                     'editgroup_id': '2pwc42gbkfhwxhod3hyqrgo544',
                     'index': 576,
                     'timestamp': datetime.datetime(2019, 1, 31, 0, 11, 52, 594740, tzinfo=tzutc())},
 'edit': {'edit_id': '8302af41-c1fa-4f87-a5c6-0ffa29cc5998',
          'editgroup_id': '2pwc42gbkfhwxhod3hyqrgo544',
          'extra': None,
          'ident': 'bi7rkf2w6jc5fd6z2szjd4k7j4',
          'prev_revision': None,
          'redirect_ident': None,
          'revision': 'e4d6f182-1de6-4ea6-a44d-42ef3744a239'},
 'editgroup': {'annotations': None,
               'changelog_index': 576,
               'created': datetime.datetime(2019, 1, 31, 0, 11, 52, 594740, tzinfo=tzutc()),
               'description': 'Automated import of container-level metadata, '
                              'by ISSN. Metadata from Internet Archive '
                              'munging.',
               'editgroup_id': '2pwc42gbkfhwxhod3hyqrgo544',
               'editor': {'editor_id': '4ravvsiw3rbypj2ltuugvtw6nu',
                          'is_active': True,
                          'is_admin': True,
                          'is_bot': True,
                          'username': 'journal-metadata-bot'},
               'editor_id': '4ravvsiw3rbypj2ltuugvtw6nu',
               'edits': None,
               'extra': {'agent': 'fatcat_tools.JournalMetadataImporter',
                         'git_rev': '1fe3712'},
               'submitted': None}}]

CREATOR_HISTORY = [{'changelog_entry': {'editgroup': None,
                     'editgroup_id': 'ynn4nvuwafdtxiqboq7wzcarz4',
                     'index': 2796,
                     'timestamp': datetime.datetime(2019, 1, 31, 0, 50, 49, 484237, tzinfo=tzutc())},
 'edit': {'edit_id': 'd34bb9c3-f5bf-4cbc-8456-1edede489ea0',
          'editgroup_id': 'ynn4nvuwafdtxiqboq7wzcarz4',
          'extra': None,
          'ident': 'youvaikdxnfbrdze4dmlhqtpji',
          'prev_revision': None,
          'redirect_ident': None,
          'revision': '71f111cf-af32-4e80-b45f-ea5c4f94ea25'},
 'editgroup': {'annotations': None,
               'changelog_index': 2796,
               'created': datetime.datetime(2019, 1, 31, 0, 50, 49, 484237, tzinfo=tzutc()),
               'description': 'Automated import of ORCID metadata, from '
                              'official bulk releases.',
               'editgroup_id': 'ynn4nvuwafdtxiqboq7wzcarz4',
               'editor': {'editor_id': 'yxggpphfqzd4dmomhjw5qh6apa',
                          'is_active': True,
                          'is_admin': True,
                          'is_bot': True,
                          'username': 'orcid-bot'},
               'editor_id': 'yxggpphfqzd4dmomhjw5qh6apa',
               'edits': None,
               'extra': {'agent': 'fatcat_tools.OrcidImporter',
                         'git_rev': '1fe3712'},
               'submitted': None}}]

FILE_HISTORY = [{'changelog_entry': {'editgroup': None,
                     'editgroup_id': 'bjiovs43zbf75pxze3udalm27a',
                     'index': 4873842,
                     'timestamp': datetime.datetime(2020, 10, 12, 12, 8, 3, 218146, tzinfo=tzutc())},
 'edit': {'edit_id': 'ffa2545c-e49f-4a95-9124-db947e297cab',
          'editgroup_id': 'bjiovs43zbf75pxze3udalm27a',
          'extra': {'ingest_request_source': 'fatcat-ingest',
                    'link_source': 'doi',
                    'link_source_id': '10.21061/alan.v32i2.a.5'},
          'ident': 'y6k6estkpbdrpmdjcw2cbjvpmu',
          'prev_revision': None,
          'redirect_ident': None,
          'revision': 'cb0f27cf-038f-436f-b9fb-d45b5670fa4e'},
 'editgroup': {'annotations': None,
               'changelog_index': 4873842,
               'created': datetime.datetime(2020, 10, 12, 12, 8, 3, 218146, tzinfo=tzutc()),
               'description': 'Files crawled from web using sandcrawler ingest '
                              'tool',
               'editgroup_id': 'bjiovs43zbf75pxze3udalm27a',
               'editor': {'editor_id': 'scmbogxw25evtcesfcab5qaboa',
                          'is_active': True,
                          'is_admin': True,
                          'is_bot': True,
                          'username': 'crawl-bot'},
               'editor_id': 'scmbogxw25evtcesfcab5qaboa',
               'edits': None,
               'extra': {'agent': 'fatcat_tools.IngestFileResultImporter',
                         'git_rev': 'v0.3.2-246-gd0f4155'},
               'submitted': None}}]

FILESET_HISTORY = [{'changelog_entry': {'editgroup': None,
                     'editgroup_id': 'xl3rz6uxfrb2pgprzxictbkvxi',
                     'index': 2336005,
                     'timestamp': datetime.datetime(2019, 3, 20, 6, 13, 16, 984995, tzinfo=tzutc())},
 'edit': {'edit_id': '3d5132e3-557e-4720-ad4a-3c8cc1352a09',
          'editgroup_id': 'xl3rz6uxfrb2pgprzxictbkvxi',
          'extra': None,
          'ident': 'ho376wmdanckpp66iwfs7g22ne',
          'prev_revision': None,
          'redirect_ident': None,
          'revision': 'e07ab7b0-bc0e-4da2-9121-542263e84e2d'},
 'editgroup': {'annotations': None,
               'changelog_index': 2336005,
               'created': datetime.datetime(2019, 3, 20, 6, 8, 55, 171006, tzinfo=tzutc()),
               'description': 'One-off import of dataset(s) from CDL/DASH '
                              'repository (via IA, Dat dweb pilot project)',
               'editgroup_id': 'xl3rz6uxfrb2pgprzxictbkvxi',
               'editor': {'editor_id': '6nk42dmrifbtlarlmhgzhfdyam',
                          'is_active': True,
                          'is_admin': True,
                          'is_bot': False,
                          'username': 'bnewbold-archive'},
               'editor_id': '6nk42dmrifbtlarlmhgzhfdyam',
               'edits': None,
               'extra': {'agent': 'fatcat_tools.auto_cdl_dash_dat',
                         'git_rev': 'v0.2.0-136-g0e914e4'},
               'submitted': None}}]

WEBCAPTURE_HISTORY = [{'changelog_entry': {'editgroup': None,
                     'editgroup_id': 'kpuel5gcgjfrzkowokq54k633q',
                     'index': 2336002,
                     'timestamp': datetime.datetime(2019, 3, 20, 1, 42, 41, 371636, tzinfo=tzutc())},
 'edit': {'edit_id': '780958af-cc2a-4a97-ac55-e86ab670edd0',
          'editgroup_id': 'kpuel5gcgjfrzkowokq54k633q',
          'extra': None,
          'ident': 'z7uaeatyvfgwdpuxtrdu4okqii',
          'prev_revision': None,
          'redirect_ident': None,
          'revision': '6019e2a1-3503-4e91-97ec-5fba3abc70af'},
 'editgroup': {'annotations': None,
               'changelog_index': 2336002,
               'created': datetime.datetime(2019, 3, 20, 1, 37, 25, 552961, tzinfo=tzutc()),
               'description': 'One-off import of static web content from '
                              'wayback machine',
               'editgroup_id': 'kpuel5gcgjfrzkowokq54k633q',
               'editor': {'editor_id': '6nk42dmrifbtlarlmhgzhfdyam',
                          'is_active': True,
                          'is_admin': True,
                          'is_bot': False,
                          'username': 'bnewbold-archive'},
               'editor_id': '6nk42dmrifbtlarlmhgzhfdyam',
               'edits': None,
               'extra': {'agent': 'fatcat_tools.auto_wayback_static',
                         'git_rev': 'v0.2.0-122-gd9f9a84'},
               'submitted': None}}]


RELEASE_HISTORY = [{'changelog_entry': {'editgroup': None,
                     'editgroup_id': 'h32n3zxlfvforca3oefqdxc3lm',
                     'index': 4529728,
                     'timestamp': datetime.datetime(2020, 5, 30, 0, 13, 32, 463710, tzinfo=tzutc())},
 'edit': {'edit_id': '8f7298b7-0569-4458-af10-3366f8938f62',
          'editgroup_id': 'h32n3zxlfvforca3oefqdxc3lm',
          'extra': None,
          'ident': 'lxlaizvcuzcz7jnvt3vmubulau',
          'prev_revision': None,
          'redirect_ident': None,
          'revision': 'e395ed84-fe9f-4e8b-b9fe-340693a8c2bd'},
 'editgroup': {'annotations': None,
               'changelog_index': 4529728,
               'created': datetime.datetime(2020, 5, 30, 0, 13, 32, 463710, tzinfo=tzutc()),
               'description': 'Automated import of Crossref DOI metadata, '
                              'harvested from REST API',
               'editgroup_id': 'h32n3zxlfvforca3oefqdxc3lm',
               'editor': {'editor_id': '4onf5ix72zholapksnjgr2n47m',
                          'is_active': True,
                          'is_admin': True,
                          'is_bot': True,
                          'username': 'crossref-bot'},
               'editor_id': '4onf5ix72zholapksnjgr2n47m',
               'edits': None,
               'extra': {'agent': 'fatcat_tools.CrossrefImporter',
                         'git_rev': 'v0.3.1-414-g6e7f02d'},
               'submitted': None}}]

WORK_HISTORY = [{'changelog_entry': {'editgroup': None,
                     'editgroup_id': 'h32n3zxlfvforca3oefqdxc3lm',
                     'index': 4529728,
                     'timestamp': datetime.datetime(2020, 5, 30, 0, 13, 32, 463710, tzinfo=tzutc())},
 'edit': {'edit_id': '915014f6-c531-4f9e-9d6d-ad23600144b7',
          'editgroup_id': 'h32n3zxlfvforca3oefqdxc3lm',
          'extra': None,
          'ident': '66bwrvmzprgczh7zip5prcjimy',
          'prev_revision': None,
          'redirect_ident': None,
          'revision': 'fada2825-a980-4ae4-853f-e3fb52540a6a'},
 'editgroup': {'annotations': None,
               'changelog_index': 4529728,
               'created': datetime.datetime(2020, 5, 30, 0, 13, 32, 463710, tzinfo=tzutc()),
               'description': 'Automated import of Crossref DOI metadata, '
                              'harvested from REST API',
               'editgroup_id': 'h32n3zxlfvforca3oefqdxc3lm',
               'editor': {'editor_id': '4onf5ix72zholapksnjgr2n47m',
                          'is_active': True,
                          'is_admin': True,
                          'is_bot': True,
                          'username': 'crossref-bot'},
               'editor_id': '4onf5ix72zholapksnjgr2n47m',
               'edits': None,
               'extra': {'agent': 'fatcat_tools.CrossrefImporter',
                         'git_rev': 'v0.3.1-414-g6e7f02d'},
               'submitted': None}}]

EG_RELEASE = fcapi.ReleaseEntity(
  abstracts=[],
  container=fcapi.ContainerEntity(
      container_type='journal',
      edit_extra=None,
      extra={'abbrev': 'J. Wildl. Manage.',
             'country': 'us',
             'ezb': {'color': 'red', 'ezb_id': '65620'},
             'ia': {'sim': {'peer_reviewed': True,
                            'pub_type': 'Scholarly Journals',
                            'scholarly_peer_reviewed': True,
                            'sim_pubid': '1941',
                            'year_spans': [[1937, 2013]]}},
             'kbart': {'clockss': {'year_spans': [[2004, 2022]]},
                       'jstor': {'year_spans': [[1937, 2019]]},
                       'lockss': {'year_spans': [[2004, 2011]]},
                       'portico': {'year_spans': [[2004, 2022]]},
                       'scholarsportal': {'year_spans': [[1983, 1983],
                                                         [2004, 2012]]}},
             'languages': ['en'],
             'publisher_type': 'big5',
             'sherpa_romeo': {'color': 'yellow'},
             'urls': ['http://onlinelibrary.wiley.com/journal/10.1002/(ISSN)1937-2817',
                      'https://onlinelibrary.wiley.com/journal/19372817',
                      'http://www.bioone.org/loi/wild',
                      'https://www.jstor.org/journal/jwildmana',
                      'http://www.jstor.org/journals/0022541X.html']},
      ident='oodltuhrwvaw7l3ndtfiux4beu',
      issne='1937-2817',
      issnl='0022-541X',
      issnp='0022-541X',
      name='Journal of Wildlife Management',
      publication_status=None,
      publisher='Wiley (Blackwell Publishing)',
      redirect=None,
      revision='0c534ee9-1922-46b4-acd0-509924666b09',
      state='active',
      wikidata_qid='Q3186954'),
  container_id='oodltuhrwvaw7l3ndtfiux4beu',
  contribs=[fcapi.ReleaseContrib(
              creator=None,
              creator_id=None,
              extra={'seq': 'first'},
              given_name=None,
              index=0,
              raw_affiliation=None,
              raw_name='Clinton J. Faas',
              role='author',
              surname=None),
            fcapi.ReleaseContrib(
              creator=None,
              creator_id=None,
              extra=None,
              given_name=None,
              index=1,
              raw_affiliation=None,
              raw_name='Floyd W. Weckerly',
              role='author',
              surname=None)],
  edit_extra=None,
  ext_ids=fcapi.ReleaseExtIds(
            ark=None,
            arxiv=None,
            core=None,
            dblp=None,
            doaj=None,
            doi='10.2193/2009-135',
            hdl=None,
            isbn13=None,
            jstor=None,
            mag=None,
            oai=None,
            pmcid=None,
            pmid=None,
            wikidata_qid=None),
  extra={'crossref': {'alternative-id': ['10.2193/2009-135'],
                      'type': 'journal-article'}},
  files=[fcapi.FileEntity(
           content_scope=None,
           edit_extra=None,
           extra={},
           ident='npmfcyu6crefvj5nbtazthmu7a',
           md5='d1f5cf26d374946b56a9a665e19db4cf',
           mimetype='application/pdf',
           redirect=None,
           release_ids=['fk2np5v5mjepxpa2cbfw4adn7q'],
           releases=None,
           revision='90f13c8c-ad5f-41e5-8b89-3c9169a4f5e0',
           sha1='20278504f6df66007fc2f00a1388df340c75a7be',
           sha256='0070d7f34580b388927b1b9b1bb4ca18fd4d07246efeafd4ff878c4e066b1cdf',
           size=927316,
           state='active',
           urls=[]),
         fcapi.FileEntity(
           content_scope=None,
           edit_extra=None,
           extra={},
           ident='wxtg37omyfcipkbifd5mspegiu',
           md5='e87ece0171b54a3a4f071b912d313b7e',
           mimetype='application/pdf',
           redirect=None,
           release_ids=['fk2np5v5mjepxpa2cbfw4adn7q',
                          'ptd6b4k4djg53jphpuw3ebykzm'],
           releases=None,
           revision='422ff093-92bd-4b8a-8bfe-0afa80b7bd4d',
           sha1='f5045d3a84fa323406b73325917a21f072b5a1bc',
           sha256='8175b2e6f9bf223b85a94f8563b0348e91b7e58e94e9118d8426012eb875efbc',
           size=970204,
           state='active',
           urls=[fcapi.FileUrl(
                   rel='webarchive',
                   url='https://web.archive.org/web/20170812140139/http://www.scielo.br/pdf/bn/v11n3/a32v11n3.pdf'),
                 fcapi.FileUrl(
                   rel='repository',
                   url='http://www.scielo.br/pdf/bn/v11n3/a32v11n3.pdf')]),
           fcapi.FileEntity(
             content_scope=None,
             edit_extra=None,
             extra=None,
             ident='h7h2bvnmnnc2lhzjtrvame2duq',
             md5='54a7c43c9325c19f0d6691b7800dd7cc',
             mimetype='application/pdf',
             redirect=None,
             release_ids=['fk2np5v5mjepxpa2cbfw4adn7q'],
             releases=None,
             revision='4a9395db-9eaf-4c25-a26b-7f248fca7fe5',
             sha1='906e925da6439d46a0083633842ca72f8a98ac3f',
             sha256='f0a9c12cc57a9e9aea77a47778bf03b90081ff371503079093a348a5a44aead5',
             size=923785,
             state='active',
             urls=[fcapi.FileUrl(
                     rel='webarchive',
                     url='https://web.archive.org/web/20170809052740/http://gato-docs.its.txstate.edu/jcr:42d86f25-b20b-4fec-969e-7796ea6685ed/Faas%20and%20Weckerly%202010.pdf'),
                   fcapi.FileUrl(
                     rel='web',
                     url='http://gato-docs.its.txstate.edu/biology/faculty-s-documents-on-their-web-page/Floyd-Weckerly/Faas-and-Weckerly-2010/Faas%20and%20Weckerly%202010.pdf'),
                   fcapi.FileUrl(
                     rel='web',
                     url='http://gato-docs.its.txstate.edu/jcr:42d86f25-b20b-4fec-969e-7796ea6685ed/Faas%20and%20Weckerly%202010.pdf'),
                   fcapi.FileUrl(
                     rel='webarchive',
                     url='https://web.archive.org/web/20150918220712/http://gato-docs.its.txstate.edu/biology/faculty-s-documents-on-their-web-page/Floyd-Weckerly/Faas-and-Weckerly-2010/Faas%20and%20Weckerly%202010.pdf'),
                   fcapi.FileUrl(
                     rel='webarchive',
                     url='https://web.archive.org/web/20170812033927/http://gato-docs.its.txstate.edu/biology/faculty-s-documents-on-their-web-page/Floyd-Weckerly/Faas-and-Weckerly-2010/Faas%20and%20Weckerly%202010.pdf')]),
           fcapi.FileEntity(
             content_scope=None,
             edit_extra=None,
             extra=None,
             ident='rvr4sjwtnbcznacc2wh6rkjcfa',
             md5='6ac03aa68e5a7fd66f3906c3051f630f',
             mimetype='application/pdf',
             redirect=None,
             release_ids=['fk2np5v5mjepxpa2cbfw4adn7q'],
             releases=None,
             revision='3cbb2866-e75b-470f-a145-1f168eca238b',
             sha1='927b1ad56a105e06a9a1885e50c51199538245eb',
             sha256='58f81101b85357b1849289fa9395f11a30e9ed70da7c42546526c9651db1a13a',
             size=1292926,
             state='active',
             urls=[fcapi.FileUrl(
                     rel='web',
                     url='http://www.biotaneotropica.org.br/v11n3/pt/fullpaper?bn00611032011+en'),
                   fcapi.FileUrl(
                     rel='webarchive',
                     url='https://web.archive.org/web/20180415011348/http://www.biotaneotropica.org.br/v11n3/pt/fullpaper?bn00611032011+en')])],
  filesets=[],
  ident='fk2np5v5mjepxpa2cbfw4adn7q',
  issue=None,
  language='en',
  license_slug=None,
  number=None,
  original_title=None,
  pages='698-706',
  publisher='Wiley',
  redirect=None,
  refs=[],
  release_date=None,
  release_stage='published',
  release_type='article-journal',
  release_year=2010,
  revision='7e32011c-4c87-4dea-b4c9-3a9e0e565b11',
  state='active',
  subtitle=None,
  title='Habitat Interference by Axis Deer on White-Tailed Deer',
  version=None,
  volume='74',
  webcaptures=[],
  withdrawn_date=None,
  withdrawn_status=None,
  withdrawn_year=None,
  work_id='bkzhp3ghy5f6bcjydfz3qojkly')

@pytest.fixture
def editgroup():
    return fcapi.Editgroup(
            annotations=None,
            changelog_index=4529728,
            created=datetime.datetime(2020, 5, 30, 0, 13, 32, 463710, tzinfo=tzutc()),
            description='Automated import of Crossref DOI metadata, '
                        'harvested from REST API',
            editgroup_id='g4uijctf2nahznuvc2xxm5i5he',
            editor=fcapi.Editor(
                editor_id='4onf5ix72zholapksnjgr2n47m',
                is_active=True,
                is_admin=True,
                is_bot=True,
                username='crossref-bot'),
            editor_id='4onf5ix72zholapksnjgr2n47m',
            edits=fcapi.EditgroupEdits(
                containers=[
                    fcapi.EntityEdit(
                        edit_id='1a080f79-ffe3-4174-87bc-10ea615533e2',
                        editgroup_id='g4uijctf2nahznuvc2xxm5i5he',
                        extra=None,
                        ident="bi7rkf2w6jc5fd6z2szjd4k7j4",
                        prev_revision='f89ccd2e-a761-4b41-ba2d-313bfb42c7b7',
                        redirect_ident=None,
                        revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
                    ),
                ],
                creators=[
                    fcapi.EntityEdit(
                        edit_id='1a080f79-ffe3-4174-87bc-10ea615533e2',
                        editgroup_id='g4uijctf2nahznuvc2xxm5i5he',
                        extra=None,
                        ident="iimvc523xbhqlav6j3sbthuehu",
                        prev_revision='f89ccd2e-a761-4b41-ba2d-313bfb42c7b7',
                        redirect_ident=None,
                        revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
                        ),
                    ],
                files=[
                    fcapi.EntityEdit(
                        edit_id='1a080f79-ffe3-4174-87bc-10ea615533e2',
                        editgroup_id='g4uijctf2nahznuvc2xxm5i5he',
                        extra=None,
                        ident="y6k6estkpbdrpmdjcw2cbjvpmu",
                        prev_revision='f89ccd2e-a761-4b41-ba2d-313bfb42c7b7',
                        redirect_ident=None,
                        revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
                        ),
                    ],
                filesets=[
                    fcapi.EntityEdit(
                        edit_id='1a080f79-ffe3-4174-87bc-10ea615533e2',
                        editgroup_id='g4uijctf2nahznuvc2xxm5i5he',
                        extra=None,
                        ident="ho376wmdanckpp66iwfs7g22ne",
                        prev_revision='f89ccd2e-a761-4b41-ba2d-313bfb42c7b7',
                        redirect_ident=None,
                        revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
                        ),
                    ],
                webcaptures=[
                    fcapi.EntityEdit(
                        edit_id='1a080f79-ffe3-4174-87bc-10ea615533e2',
                        editgroup_id='g4uijctf2nahznuvc2xxm5i5he',
                        extra=None,
                        ident="z7uaeatyvfgwdpuxtrdu4okqii",
                        prev_revision='f89ccd2e-a761-4b41-ba2d-313bfb42c7b7',
                        redirect_ident=None,
                        revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
                        ),
                    ],
                works=[
                    fcapi.EntityEdit(
                        edit_id='1a080f79-ffe3-4174-87bc-10ea615533e2',
                        editgroup_id='g4uijctf2nahznuvc2xxm5i5he',
                        extra=None,
                        ident="uggz4zervvgevn4gt7odo4ufnq",
                        prev_revision='f89ccd2e-a761-4b41-ba2d-313bfb42c7b7',
                        redirect_ident=None,
                        revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
                        ),
                    ],
                releases=[
                    fcapi.EntityEdit(
                        edit_id='1a080f79-ffe3-4174-87bc-10ea615533e2',
                        editgroup_id='g4uijctf2nahznuvc2xxm5i5he',
                        extra=None,
                        ident='aney5kqnxvbwnn3aasq7uvup6m',
                        prev_revision='f89ccd2e-a761-4b41-ba2d-313bfb42c7b7',
                        redirect_ident=None,
                        revision='198c87e7-9124-4371-b34a-cb5e75bbb77c',
                        ),
                    ]),
            extra={'agent': 'fatcat_tools.CrossrefImporter',
                   'git_rev': 'v0.3.1-414-g6e7f02d'},
            submitted=None)
