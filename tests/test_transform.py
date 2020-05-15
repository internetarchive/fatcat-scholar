
import pytest
from fatcat_openapi_client import ReleaseEntity

from fatcat_scholar.es_transform import *
from fatcat_scholar.api_entities import *

def test_es_release_from_release():

    with open('tests/files/release_hsmo6p4smrganpb3fndaj2lon4.json', 'r') as f:
        release = entity_from_json(f.read(), ReleaseEntity)
    
    obj = es_release_from_release(release)
    d = json.loads(obj.json())

    assert obj.ident == release.ident == "hsmo6p4smrganpb3fndaj2lon4"
    assert obj.ident == release.ident == d['ident'] == "hsmo6p4smrganpb3fndaj2lon4"
    assert obj.doi_registrar == "crossref"
    assert obj.doi_prefix == "10.7717"
