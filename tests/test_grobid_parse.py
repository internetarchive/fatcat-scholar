from grobid_tei_xml import parse_document_xml


def test_grobid_parse_legacy() -> None:
    """
    This function formerly tested the grobid2json file in this project. Now it
    tests backwards-compatibility of the grobid_tei_xml library.
    """

    with open("tests/files/example_grobid.tei.xml", "r") as f:
        blob = f.read()

    doc = parse_document_xml(blob)
    obj = doc.to_legacy_dict()

    assert (
        obj["title"]
        == "Changes of patients' satisfaction with the health care services in Lithuanian Health Promoting Hospitals network"
    )

    ref = [c for c in obj["citations"] if c["id"] == "b12"][0]
    assert ref["authors"][0] == {"given_name": "K", "name": "K Tasa", "surname": "Tasa"}
    assert ref["journal"] == "Quality Management in Health Care"
    assert ref["title"] == "Using patient feedback for quality improvement"
    assert ref["date"] == "1996"
    assert ref["pages"] == "206-225"
    assert ref["volume"] == "8"
    assert (
        ref["unstructured"]
        == "Tasa K, Baker R, Murray M. Using patient feedback for qua- lity improvement. Quality Management in Health Care 1996;8:206-19."
    )


def test_grobid_parse() -> None:
    """
    Equivalent to test_grobid_parse_legacy(), but using the GrobidDocument type directly
    """

    with open("tests/files/example_grobid.tei.xml", "r") as f:
        blob = f.read()

    doc = parse_document_xml(blob)

    assert (
        doc.header.title
        == "Changes of patients' satisfaction with the health care services in Lithuanian Health Promoting Hospitals network"
    )

    assert doc.citations is not None
    ref = [c for c in doc.citations if c.id == "b12"][0]
    assert ref.authors[0].given_name == "K"
    assert ref.authors[0].full_name == "K Tasa"
    assert ref.authors[0].surname == "Tasa"
    assert ref.journal == "Quality Management in Health Care"
    assert ref.title == "Using patient feedback for quality improvement"
    assert ref.date == "1996"
    assert ref.pages == "206-225"
    assert ref.volume == "8"
    assert (
        ref.unstructured
        == "Tasa K, Baker R, Murray M. Using patient feedback for qua- lity improvement. Quality Management in Health Care 1996;8:206-19."
    )
