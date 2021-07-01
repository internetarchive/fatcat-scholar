from fatcat_openapi_client import ReleaseEntity

from fatcat_scholar.grobid2json import teixml2json
from fatcat_scholar.transform import refs_from_grobid


def test_transform_refs_grobid() -> None:

    with open("tests/files/example_grobid.tei.xml", "r") as f:
        blob = f.read()

    dummy_release = ReleaseEntity(
        ident="releasedummy22222222222222",
        work_id="workdummy22222222222222222",
        release_year=1234,
        release_stage="accepted",
        ext_ids={},
    )

    tei_dict = teixml2json(blob, True)
    refs = refs_from_grobid(dummy_release, tei_dict)

    ref = refs[12]
    assert ref.release_ident == "releasedummy22222222222222"
    assert ref.work_ident == "workdummy22222222222222222"
    assert ref.release_stage == "accepted"
    assert ref.release_year == 1234
    assert ref.ref_source == "grobid"
    assert ref.key == "b12"
    assert ref.index == 12
    assert ref.locator == None
    assert ref.biblio.contrib_raw_names is not None
    assert ref.biblio.contrib_raw_names[0] == "K Tasa"
    assert ref.biblio.container_name == "Quality Management in Health Care"
    assert ref.biblio.title == "Using patient feedback for quality improvement"
    assert ref.biblio.year == 1996
    assert ref.biblio.pages == "206-225"
    assert ref.biblio.volume == "8"
    assert (
        ref.biblio.unstructured
        == "Tasa K, Baker R, Murray M. Using patient feedback for qua- lity improvement. Quality Management in Health Care 1996;8:206-19."
    )
