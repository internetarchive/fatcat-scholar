from fatcat_scholar.grobid2json import teixml2json


def test_grobid_teixml2json() -> None:

    with open("tests/files/example_grobid.tei.xml", "r") as f:
        blob = f.read()

    obj = teixml2json(blob, True)

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
