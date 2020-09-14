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
        ext_ids={},
    )

    tei_dict = teixml2json(blob, True)
    refs = refs_from_grobid(dummy_release, tei_dict)

    ref = refs[12].biblio
    assert ref.contrib_raw_names is not None
    assert ref.contrib_raw_names[0] == "K Tasa"
    assert ref.container_name == "Quality Management in Health Care"
    assert ref.title == "Using patient feedback for quality improvement"
    assert ref.year == 1996
    assert ref.pages == "206-225"
    assert ref.volume == "8"
    assert (
        ref.unstructured
        == "Tasa K, Baker R, Murray M. Using patient feedback for qua- lity improvement. Quality Management in Health Care 1996;8:206-19."
    )
