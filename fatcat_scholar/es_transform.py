
"""
Originally wrote these as dataclasses using pydantic.dataclasses, but we don't
get serialization for free with those. This is useful for things like
auto-conversion of datetime objects.
"""

import typing
import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from fatcat_openapi_client import ReleaseEntity


class DocType(str, Enum):
    work = "work"
    sim_page = "sim_page"

class AccessType(str, Enum):
    ia_sim = "ia_sim"
    ia_file = "ia_file"
    wayback = "wayback"
    repository = "repository"
    paywall = "paywall"
    loginwall = "loginwall"
    shadow = "shadow"

class ScholarBiblio(BaseModel):
    release_ident: Optional[str]
    title: str
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
    volume_int: Optional[str]   # TODO: needed?
    issue: Optional[str]
    issue_int: Optional[str]    # TODO: needed?
    pages: Optional[str]
    first_page: Optional[str]
    first_page_int: Optional[str] # TODO: needed?
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
    mimetype: str
    file_ident: Optional[str]
    release_ident: Optional[str]

class ScholarDoc(BaseModel):
    key: str
    doc_type: str # enum: work or page
    doc_index_ts: datetime.datetime
    work_ident: Optional[str]
    tags: List[str] = []

    biblio: ScholarBiblio
    fulltext: ScholarFulltext
    ia_sim: ScholarSim
    abstracts: List[ScholarAbstract]
    releases: List[ScholarRelease]
    access: List[ScholarAccess]

# TODO:
# es_biblio_from_release
# es_release_from_release
# es_abstracts_from_release

def doi_split_prefix(doi: str) -> str:
    return doi.split('/')[0]

def release_doi_registrar(release: ReleaseEntity) -> Optional[str]:
    if not release.ext_ids.doi or not release.extra:
        return None
    for registrar in ('crossref', 'datacite', 'jalc'):
        if registrar in release.extra:
            return registrar
    # TODO: should we default to Crossref?
    return None

#def es_biblio_from_release(release: Release) -> ScholarBiblio:

def es_release_from_release(release: ReleaseEntity) -> ScholarRelease:

    if release.container:
        container_name = release.container.name
        container_ident = release.container.ident
        container_issnl = release.container.issnl
        container_type = release.container.container_type
    else:
        container_name = release.extra.get('container_name')
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
