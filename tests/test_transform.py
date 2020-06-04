from fatcat_openapi_client import ReleaseEntity

from fatcat_scholar.schema import *
from fatcat_scholar.api_entities import *


def test_es_release_from_release() -> None:

    with open("tests/files/release_hsmo6p4smrganpb3fndaj2lon4.json", "r") as f:
        release = entity_from_json(f.read(), ReleaseEntity)

    obj = es_release_from_release(release)
    d = json.loads(obj.json())

    assert obj.ident == release.ident == d["ident"] == "hsmo6p4smrganpb3fndaj2lon4"
    assert obj.doi_registrar == "crossref"
    assert obj.doi_prefix == "10.7717"


def test_es_biblio_from_release() -> None:

    with open("tests/files/release_hsmo6p4smrganpb3fndaj2lon4.json", "r") as f:
        release = entity_from_json(f.read(), ReleaseEntity)

    obj = es_biblio_from_release(release)
    d = json.loads(obj.json())

    assert (
        obj.release_ident
        == release.ident
        == d["release_ident"]
        == "hsmo6p4smrganpb3fndaj2lon4"
    )
