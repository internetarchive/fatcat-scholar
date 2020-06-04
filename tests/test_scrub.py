from fatcat_scholar.schema import scrub_text


def test_scrub() -> None:
    vectors = [
        (
            "“Please clean this piece… of text</b>„",
            '"Please clean this piece... of text"',
        ),
        ("<jats:p>blah", "blah"),
    ]

    for raw, fixed in vectors:
        assert fixed == scrub_text(raw)
