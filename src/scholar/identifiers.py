import re
from typing import Optional

DOI_REGEX = re.compile(r"^10.\d{3,6}/\S+$")


def clean_doi(raw: Optional[str]) -> Optional[str]:
    """
    Removes any:
    - padding whitespace
    - 'doi:' prefix
    - URL prefix

    Lower-cases the DOI.

    Does not try to un-URL-encode

    Rejects non-ASCII strings

    Returns None if not a valid DOI
    """
    if not raw:
        return None
    raw = raw.strip().lower()
    if len(raw.split()) != 1:
        return None
    if "10." not in raw:
        return None
    if not raw.startswith("10."):
        raw = raw[raw.find("10.") :]
    if raw[7:9] == "//":
        raw = raw[:8] + raw[9:]

    if not raw.startswith("10."):
        return None

    if not raw.isascii():
        return None

    if not DOI_REGEX.fullmatch(raw):
        return None

    return raw


def test_clean_doi() -> None:
    assert clean_doi(None) is None
    assert clean_doi("") is None
    assert clean_doi("asdf") is None
    assert clean_doi("10.123") is None
    assert clean_doi("10.1234/asdf ") == "10.1234/asdf"
    assert clean_doi("10.1234/ASdf ") == "10.1234/asdf"
    assert clean_doi("10.1037//0002-9432.72.1.50") == "10.1037/0002-9432.72.1.50"
    assert clean_doi("10.1037/0002-9432.72.1.50") == "10.1037/0002-9432.72.1.50"
    assert clean_doi("10.23750/abm.v88i2 -s.6506") is None
    assert clean_doi("10.17167/mksz.2017.2.129–155") is None
    assert clean_doi("http://doi.org/10.1234/asdf ") == "10.1234/asdf"
    assert clean_doi("https://dx.doi.org/10.1234/asdf ") == "10.1234/asdf"
    assert clean_doi("doi:10.1234/asdf ") == "10.1234/asdf"
    assert clean_doi("doi:10.1234/ asdf ") is None
    assert clean_doi("10.4149/gpb¬_2017042") is None  # "logical negation" character
    assert clean_doi("10.6002/ect.2020.häyry") is None  # this example via pubmed (pmid:32519616)
    # GROBID mangled DOI
    assert clean_doi("21924DOI10.1234/asdf ") == "10.1234/asdf"

ISBN13_REGEX = re.compile(r"^97(?:8|9)-\d{1,5}-\d{1,7}-\d{1,6}-\d$")

def clean_isbn13(raw: str|None) -> str|None:
    if not raw:
        return None
    raw = raw.strip()
    if not ISBN13_REGEX.fullmatch(raw):
        return None
    return raw

def test_clean_isbn13() -> None:
    assert clean_isbn13("978-1-56619-909-4") == "978-1-56619-909-4"
    assert clean_isbn13("978-1-4028-9462-6") == "978-1-4028-9462-6"
    assert clean_isbn13("978-1-56619-909-4 ") == "978-1-56619-909-4"
    assert clean_isbn13("9781566199094") is None

ARXIV_ID_REGEX = re.compile(r"^(\d{4}.\d{4,5}|[a-z\-]+(\.[A-Z]{2})?/\d{7})(v\d+)?$")

def clean_arxiv_id(raw: str|None) -> str|None:
    """
    Removes any:
    - 'arxiv:' prefix

    Works with versioned or un-versioned arxiv identifiers.

    TODO: version of this function that only works with versioned identifiers?
    That is the behavior of fatcat API
    """
    if not raw:
        return None
    raw = raw.strip()
    if raw.lower().startswith("arxiv:"):
        raw = raw[6:]
    if raw.lower().startswith("https://arxiv.org/abs/"):
        raw = raw[22:]
    if not ARXIV_ID_REGEX.fullmatch(raw):
        return None
    return raw

def test_clean_arxiv_id() -> None:
    assert clean_arxiv_id("0806.2878v1") == "0806.2878v1"
    assert clean_arxiv_id("0806.2878") == "0806.2878"
    assert clean_arxiv_id("1501.00001v1") == "1501.00001v1"
    assert clean_arxiv_id("1501.00001") == "1501.00001"
    assert clean_arxiv_id("hep-th/9901001v1") == "hep-th/9901001v1"
    assert clean_arxiv_id("hep-th/9901001") == "hep-th/9901001"
    assert clean_arxiv_id("math.CA/0611800v2") == "math.CA/0611800v2"
    assert clean_arxiv_id("math.CA/0611800") == "math.CA/0611800"
    assert clean_arxiv_id("0806.2878v1 ") == "0806.2878v1"
    assert clean_arxiv_id("cs/0207047") == "cs/0207047"

    assert clean_arxiv_id("https://arxiv.org/abs/0806.2878v1") == "0806.2878v1"
    assert clean_arxiv_id("arxiv:0806.2878v1") == "0806.2878v1"
    assert clean_arxiv_id("arXiv:0806.2878v1") == "0806.2878v1"

    assert clean_arxiv_id("hep-TH/9901001v1") is None
    assert clean_arxiv_id("hßp-th/9901001v1") is None
    assert clean_arxiv_id("math.CA/06l1800v2") is None
    assert clean_arxiv_id("mßth.ca/0611800v2") is None
    assert clean_arxiv_id("MATH.CA/0611800v2") is None
    assert clean_arxiv_id("0806.2878v23") == "0806.2878v23"  # ?
    assert clean_arxiv_id("0806.2878v") is None
    assert clean_arxiv_id("0806.2878") == "0806.2878"
    assert clean_arxiv_id("006.2878v1") is None
    assert clean_arxiv_id("0806.v1") is None
    assert clean_arxiv_id("08062878v1") is None


def clean_pmcid(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    # fatcat version does not do .upper()
    raw = raw.strip().upper()
    if len(raw.split()) != 1:
        return None
    if raw.startswith("PMC") and raw[3:] and raw[3:].isdigit():
        return raw
    return None


def test_clean_pmcid() -> None:
    assert clean_pmcid("10.1234/asdf ") is None
    assert clean_pmcid("") is None
    assert clean_pmcid("1 2") is None
    assert clean_pmcid(None) is None
    assert clean_pmcid("PMC123") == "PMC123"
    assert clean_pmcid("pmc123") == "PMC123"


ISSN_REGEX = re.compile(r"^\d{4}-\d{3}[0-9X]$")

def clean_issn(raw: str|None) -> str|None:
    if not raw:
        return None
    raw = raw.strip().upper()
    if len(raw) != 9:
        return None
    if not ISSN_REGEX.fullmatch(raw):
        return None
    return raw


def test_clean_issn() -> None:
    assert clean_issn("1234-4567") == "1234-4567"
    assert clean_issn("1234-456X") == "1234-456X"
    assert clean_issn("134-4567") is None
    assert clean_issn("123X-4567") is None

def clean_sha1(raw: str|None) -> str|None:
    if not raw:
        return None
    raw = raw.strip().lower()
    if len(raw.split()) != 1:
        return None
    if len(raw) != 40:
        return None
    for c in raw:
        if c not in "0123456789abcdef":
            return None
    return raw


def test_clean_sha1() -> None:
    assert (
        clean_sha1("0fba3fba0e1937aa0297de3836b768b5dfb23d7b")
        == "0fba3fba0e1937aa0297de3836b768b5dfb23d7b"
    )
    assert (
        clean_sha1("0fba3fba0e1937aa0297de3836b768b5dfb23d7b ")
        == "0fba3fba0e1937aa0297de3836b768b5dfb23d7b"
    )
    assert clean_sha1("fba3fba0e1937aa0297de3836b768b5dfb23d7b") is None
    assert clean_sha1("qfba3fba0e1937aa0297de3836b768b5dfb23d7b") is None
    assert clean_sha1("0fba3fb a0e1937aa0297de3836b768b5dfb23d7b") is None

def clean_sha256(raw: str|None) -> str|None:
    if not raw:
        return None
    raw = raw.strip().lower()
    if len(raw.split()) != 1:
        return None
    if len(raw) != 64:
        return None
    for c in raw:
        if c not in "0123456789abcdef":
            return None
    return raw


def test_clean_sha256() -> None:
    assert (
        clean_sha256("6cc853f2ae75696b2e45f476c76b946b0fc2df7c52bb38287cb074aceb77bc7f")
        == "6cc853f2ae75696b2e45f476c76b946b0fc2df7c52bb38287cb074aceb77bc7f"
    )
    assert clean_sha256("0fba3fba0e1937aa0297de3836b768b5dfb23d7b") is None


ORCID_REGEX = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")

def clean_orcid(raw: str|None) -> str|None:
    if not raw:
        return None
    raw = raw.strip()
    if not ORCID_REGEX.fullmatch(raw):
        return None
    return raw

def test_clean_orcid() -> None:
    assert clean_orcid("0123-4567-3456-6789") == "0123-4567-3456-6789"
    assert clean_orcid("0123-4567-3456-678X") == "0123-4567-3456-678X"
    assert clean_orcid("0123-4567-3456-6789 ") == "0123-4567-3456-6789"
    assert clean_orcid("01234567-3456-6780") is None
    assert clean_orcid("0x23-4567-3456-6780") is None

