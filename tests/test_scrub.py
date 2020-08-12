from fatcat_scholar.schema import scrub_text, clean_str


def test_scrub() -> None:
    vectors = [
        (
            "“Please clean this piece… of text</b>„",
            '"Please clean this piece... of text"',
        ),
        ("<jats:p>blah thing", "blah thing"),
    ]

    for raw, fixed in vectors:
        assert fixed == scrub_text(raw)


def test_clean_str() -> None:
    vectors = [
        (
            "Di� Hekimli�i Fak�ltesi ��rencilerinde Temporomandibular Eklem Rahats�zl�klar�n�n ve A��z Sa�l��� Al��kanl�klar�n�n De�erlendirilmesi",
            "Di� Hekimli�i Fak�ltesi ��rencilerinde Temporomandibular Eklem Rahats�zl�klar�n�n ve A��z Sa�l��� Al��kanl�klar�n�n De�erlendirilmesi",
        ),
        ("<jats:p>blah thing", "blah thing"),
        ("title with <i>italics</i>", "title with italics"),
        ("title with <sup>partial super", "title with partial super"),
        ("", None),
        ("&NA", None),
        (None, None),
    ]

    for raw, fixed in vectors:
        assert fixed == clean_str(raw)
