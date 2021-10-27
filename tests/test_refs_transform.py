import json

from fatcat_openapi_client import ReleaseEntity

from fatcat_scholar.grobid2json import teixml2json
from fatcat_scholar.transform import refs_from_crossref, refs_from_grobid


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
    assert ref.index == 13
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


def test_transform_refs_crossref() -> None:

    with open("tests/files/example_crossref_record.json", "r") as f:
        record = json.loads(f.read())

    dummy_release = ReleaseEntity(
        ident="releasedummy22222222222222",
        work_id="workdummy22222222222222222",
        release_year=1234,
        release_stage="accepted",
        ext_ids={},
    )

    refs = refs_from_crossref(dummy_release, record)

    assert refs[0].release_ident == "releasedummy22222222222222"
    assert refs[0].work_ident == "workdummy22222222222222222"
    assert refs[0].release_stage == "accepted"
    assert refs[0].release_year == 1234
    assert refs[0].ref_source == "crossref"
    assert refs[0].key == "BIB0001|his12200-cit-0001"
    assert refs[0].index == 1
    assert refs[0].locator is None
    assert refs[0].biblio.contrib_raw_names is not None
    assert refs[0].biblio.contrib_raw_names[0] == "Churg"
    assert refs[0].biblio.container_name == "Arch. Pathol. Lab. Med."
    assert (
        refs[0].biblio.title
        == "The separation of benign and malignant mesothelial proliferations"
    )
    assert refs[0].biblio.year == 2012
    assert refs[0].biblio.pages == "1217"
    assert refs[0].biblio.volume == "136"
    assert refs[0].biblio.doi == "10.5858/arpa.2012-0112-ra"
    assert refs[0].biblio.unstructured is None

    assert (
        refs[6].biblio.title
        == "Advances in Laser Remote Sensing – Selected Papers Presented at the 20th International Laser Radar Conference"
    )
    assert refs[6].biblio.year == 2001

    assert refs[7].key == "CIT0041"
    assert (
        refs[7].biblio.unstructured
        == "Linda Weiss,Creating Capitalism. Oxford: Blackwell, 1988. 272 pp. £29.95. ISBN 0 631 15733 6."
    )

    assert refs[8].key == "576_CR3"
    assert refs[8].biblio.unstructured is not None
    assert refs[8].biblio.title == "The NURBS Book, Monographs in Visual Communication"
    assert refs[8].biblio.year == 1997
    assert refs[8].biblio.version == "2"
