"""
Originally wrote these as dataclasses using pydantic.dataclasses, but we don't
get serialization for free with those. This is useful for things like
auto-conversion of datetime objects.
"""

import re
import datetime
from enum import Enum
from typing import Optional, List, Any, Dict

import ftfy
from bs4 import BeautifulSoup

# pytype: disable=import-error
from pydantic import BaseModel

# pytype: enable=import-error

from fatcat_openapi_client import ReleaseEntity, ReleaseContrib
from fatcat_scholar.api_entities import entity_to_dict


class DocType(str, Enum):
    work = "work"
    sim_page = "sim_page"


class IntermediateBundle(BaseModel):
    doc_type: DocType
    releases: List[ReleaseEntity]
    biblio_release_ident: Optional[str]
    grobid_fulltext: Optional[Dict[str, Any]]
    pdftotext_fulltext: Optional[Dict[str, Any]]
    pdf_meta: Optional[Dict[str, Any]]
    sim_fulltext: Optional[Dict[str, Any]]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ReleaseEntity: lambda re: entity_to_dict(re),
        }


class AccessType(str, Enum):
    ia_sim = "ia_sim"
    ia_file = "ia_file"
    wayback = "wayback"
    web = "web"
    repository = "repository"
    paywall = "paywall"
    loginwall = "loginwall"
    shadow = "shadow"


class ScholarBiblio(BaseModel):
    release_ident: Optional[str]
    title: Optional[str]
    subtitle: Optional[str]
    original_title: Optional[str]
    release_date: Optional[datetime.date]
    release_year: Optional[int]
    release_type: Optional[str]
    release_stage: Optional[str]
    withdrawn_status: Optional[str]
    lang_code: Optional[str]
    country_code: Optional[str]
    volume: Optional[str]
    volume_int: Optional[str]  # TODO: needed?
    issue: Optional[str]
    issue_int: Optional[str]  # TODO: needed?
    pages: Optional[str]
    first_page: Optional[str]
    first_page_int: Optional[int]  # TODO: needed?
    number: Optional[str]

    doi: Optional[str]
    doi_prefix: Optional[str]
    doi_registrar: Optional[str]
    pmid: Optional[str]
    pmcid: Optional[str]
    isbn13: Optional[str]
    wikidata_qid: Optional[str]
    arxiv_id: Optional[str]
    jstor_id: Optional[str]
    mag_id: Optional[str]

    license_slug: Optional[str]
    publisher: Optional[str]
    publisher_type: Optional[str]
    container_name: Optional[str]
    container_original_name: Optional[str]
    container_ident: Optional[str]
    container_issnl: Optional[str]
    container_wikidata_qid: Optional[str]
    issns: List[str]
    container_type: Optional[str]
    contrib_count: Optional[int]
    contrib_names: List[str]
    affiliations: List[str]


class ScholarFulltext(BaseModel):
    lang_code: Optional[str]
    body: str
    acknowledgement: Optional[str]
    annex: Optional[str]
    release_ident: Optional[str]
    file_ident: Optional[str]
    file_sha1: Optional[str]
    file_mimetype: Optional[str]
    thumbnail_url: Optional[str]
    access_url: Optional[str]
    access_type: Optional[AccessType]


class ScholarRelease(BaseModel):
    ident: Optional[str]
    revision: Optional[str]
    title: str
    release_date: Optional[datetime.date]
    release_year: Optional[int]
    release_type: Optional[str]
    release_stage: Optional[str]
    withdrawn_status: Optional[str]

    doi: Optional[str]
    doi_prefix: Optional[str]
    doi_registrar: Optional[str]
    pmid: Optional[str]
    pmcid: Optional[str]
    isbn13: Optional[str]
    wikidata_qid: Optional[str]
    arxiv_id: Optional[str]
    jstor_id: Optional[str]
    mag_id: Optional[str]

    license_slug: Optional[str]
    container_name: Optional[str]
    container_ident: Optional[str]
    container_issnl: Optional[str]
    container_type: Optional[str]


class ScholarSim(BaseModel):
    issue_item: str
    pub_collection: str
    sim_pubid: str
    first_page: Optional[str]


class ScholarAbstract(BaseModel):
    body: str
    lang_code: Optional[str]


class ScholarAccess(BaseModel):
    access_type: AccessType
    access_url: str
    mimetype: Optional[str]
    file_ident: Optional[str]
    release_ident: Optional[str]


class ScholarDoc(BaseModel):
    key: str
    doc_type: str  # enum: work or page
    doc_index_ts: datetime.datetime
    collapse_key: str
    work_ident: Optional[str]
    tags: List[str] = []

    biblio: ScholarBiblio
    fulltext: Optional[ScholarFulltext]
    ia_sim: Optional[ScholarSim]
    abstracts: List[ScholarAbstract]
    releases: List[ScholarRelease]
    access: List[ScholarAccess]


def doi_split_prefix(doi: str) -> str:
    return doi.split("/")[0]


def release_doi_registrar(release: ReleaseEntity) -> Optional[str]:
    if not release.ext_ids.doi or not release.extra:
        return None
    for registrar in ("crossref", "datacite", "jalc"):
        if registrar in release.extra:
            return registrar
    # TODO: should we default to Crossref?
    return None


UNWANTED_ABSTRACT_PREFIXES = [
    # roughly sort this long to short
    "Abstract No Abstract ",
    "Publisher Summary ",
    "Abstract ",
    "ABSTRACT ",
    "Summary ",
    "Background: ",
    "Background ",
]


def scrub_text(raw: str, mimetype: str = None) -> Optional[str]:
    """
    This function takes a mimetype-hinted string and tries to reduce it to a
    simple token-and-punctuation scheme with any and all markup removed. Eg,
    HTML tags, JATS XML tags, LaTeX, whatever.

    The output should be clean and "HTML safe" (though should still be escaped
    in HTML to get entity encoding correct).

    TODO: not using mimetype hint for latex yet
    """
    text = ftfy.fix_text(raw)

    # remove HTML
    text = BeautifulSoup(text, "html.parser").get_text()

    # TODO: for performance, compile these as globals?
    # Three regexes below adapted from Blendle cleaner.py
    # https://github.com/blendle/research-summarization/blob/master/enrichers/cleaner.py#L29
    text = re.sub(r"…", "...", text)
    text = re.sub(r"[`‘’‛⸂⸃⸌⸍⸜⸝]", "'", text)
    text = re.sub(r"[„“]|(\'\')|(,,)", '"', text)
    text = re.sub(r"\s+", " ", text).strip()

    # hack to remove abstract prefixes
    for prefix in UNWANTED_ABSTRACT_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break

    if not text:
        return None
    return text


def contrib_name(contrib: ReleaseContrib) -> str:
    # TODO: support more cultural normals for name presentation
    if contrib.raw_name:
        return contrib.raw_name
    elif contrib.given_name and contrib.surname:
        return f"{contrib.given_name} {contrib.surname}"
    elif contrib.surname:
        return contrib.surname
    else:
        return contrib.given_name


def contrib_affiliation(contrib: ReleaseContrib) -> Optional[str]:
    # TODO
    return None


def es_abstracts_from_grobid(tei_dict: dict) -> List[ScholarAbstract]:

    if tei_dict.get("abstract"):
        body = scrub_text(tei_dict["abstract"])
        if body:
            return [ScholarAbstract(lang_code=tei_dict.get("lang"), body=body)]
    return []


def es_abstracts_from_release(release: ReleaseEntity) -> List[ScholarAbstract]:

    d = dict()
    for abst in release.abstracts:
        if abst.lang not in d:
            body = scrub_text(abst.content)
            if body:
                d[abst.lang] = ScholarAbstract(
                    lang_code=abst.lang, body=scrub_text(abst.content)
                )
    return list(d.values())


def es_biblio_from_release(release: ReleaseEntity) -> ScholarBiblio:

    if release.container:
        publisher = release.publisher
        container_name = release.container.name
        container_original_name = (
            release.container.extra and release.container.extra.get("original_name")
        )
        if not container_original_name or not isinstance(container_original_name, str):
            container_original_name = None
        container_ident = release.container.ident
        container_type = release.container.container_type
        container_issnl = release.container.issnl
        issns = [
            container_issnl,
        ]
        if release.extra.get("issne"):
            issns.append(release.extra["issne"])
        if release.extra.get("issnp"):
            issns.append(release.extra["issnp"])
        issns = list(set(issns))
    else:
        publisher = release.extra.get("publisher")
        container_name = release.extra.get("container_name")
        container_original_name = None
        container_ident = None
        container_type = None
        container_issnl = None
        issns = []

    first_page: Optional[str] = None
    if release.pages:
        first_page = release.pages.split("-")[0]
    first_page_int: Optional[int] = None
    if first_page and first_page.isdigit():
        first_page_int = int(first_page)

    ret = ScholarBiblio(
        release_ident=release.ident,
        title=release.title,
        subtitle=release.subtitle,
        original_title=release.original_title,
        release_date=release.release_date,
        release_year=release.release_year,
        release_type=release.release_type,
        release_stage=release.release_stage,
        withdrawn_status=release.withdrawn_status,
        lang_code=release.language,
        country_code=release.extra and release.extra.get("country"),
        volume=release.volume,
        volume_int=None,
        issue=release.issue,
        issue_int=None,
        pages=release.pages,
        first_page=first_page,
        first_page_int=first_page_int,
        number=release.number,
        doi=release.ext_ids.doi,
        doi_prefix=release.ext_ids.doi and doi_split_prefix(release.ext_ids.doi),
        doi_registrar=release_doi_registrar(release),
        pmid=release.ext_ids.pmid,
        pmcid=release.ext_ids.pmcid,
        isbn13=release.ext_ids.isbn13,
        wikidata_qid=release.ext_ids.wikidata_qid,
        arxiv_id=release.ext_ids.arxiv,
        jstor_id=release.ext_ids.jstor,
        mag_id=release.ext_ids.mag,
        license_slug=release.license_slug,
        publisher=publisher,
        container_name=container_name,
        container_original_name=container_original_name,
        container_ident=container_ident,
        container_type=container_type,
        container_issnl=container_issnl,
        issns=issns,
        # TODO; these filters sort of meh. refactor to be above?
        contrib_names=list(
            filter(lambda x: bool(x), [contrib_name(c) for c in release.contribs])
        ),
        contrib_count=len([c for c in release.contribs if c.index]),
        affiliations=list(
            filter(
                lambda x: bool(x),
                [contrib_affiliation(c) for c in release.contribs if c.index],
            )
        ),
    )
    return ret


def es_release_from_release(release: ReleaseEntity) -> ScholarRelease:

    if release.container:
        container_name = release.container.name
        container_ident = release.container.ident
        container_issnl = release.container.issnl
        container_type = release.container.container_type
    else:
        container_name = release.extra.get("container_name")
        container_ident = None
        container_issnl = None
        container_type = None

    ret = ScholarRelease(
        ident=release.ident,
        revision=release.revision,
        title=release.title,
        release_date=release.release_date,
        release_year=release.release_year,
        release_type=release.release_type,
        release_stage=release.release_stage,
        withdrawn_status=release.withdrawn_status,
        doi=release.ext_ids.doi,
        doi_prefix=release.ext_ids.doi and doi_split_prefix(release.ext_ids.doi),
        doi_registrar=release_doi_registrar(release),
        pmid=release.ext_ids.pmid,
        pmcid=release.ext_ids.pmcid,
        isbn13=release.ext_ids.isbn13,
        wikidata_qid=release.ext_ids.wikidata_qid,
        arxiv_id=release.ext_ids.arxiv,
        jstor_id=release.ext_ids.jstor,
        mag_id=release.ext_ids.mag,
        license_slug=release.license_slug,
        container_name=container_name,
        container_ident=container_ident,
        container_issnl=container_issnl,
        container_type=container_type,
    )
    return ret
