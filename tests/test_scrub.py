
import pytest

from fatcat_scholar.schema import *


def test_scrub():
    vectors = [
        ('“Please clean this piece… of text</b>„', '"Please clean this piece... of text"'),
        ("<jats:p>blah", "blah"),
    ]

    for raw, fixed in vectors:
        assert fixed == scrub_text(raw)

