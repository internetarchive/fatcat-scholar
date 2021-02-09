import io
from fatcat_scholar.djvu import djvu_extract_leaf_texts


def test_djvu_extract_leaf_texts() -> None:

    # https://archive.org/details/ERIC_ED441501
    with open("tests/files/ERIC_ED441501_djvu.xml") as f:
        blob = f.read()

    leaves = djvu_extract_leaf_texts(io.StringIO(blob), [3, 6])
    assert 3 in leaves
    assert 6 in leaves
    assert "2. Original cataloging tools" in leaves[3]
    assert len(leaves) == 2
