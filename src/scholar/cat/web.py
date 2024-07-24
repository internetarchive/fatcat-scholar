from dataclasses import dataclass
import logging
from typing import Annotated, Any, Callable, Dict, List, Tuple, TypeAlias
from urllib.parse import quote_plus
from uuid import UUID

import citeproc_styles
import elasticsearch
from fastapi import APIRouter, Depends, Path, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import fatcat_openapi_client as fcapi
from fatcat_openapi_client import DefaultApi
from fuzzycat.grobid_unstructured import (
    grobid_api_process_citation,
    grobid_ref_to_release,
    transform_grobid_ref_xml,
)
from fuzzycat.simple import (
    close_fuzzy_biblio_matches,
    close_fuzzy_release_matches
)
from scholar.cat.search import (
        ReleaseQuery,
        GenericQuery,
        do_release_search,
        do_container_search,
        CatSearchError,
        get_elastic_container_random_releases,
        get_elastic_container_browse_year_volume_issue,
        get_elastic_container_stats,
        get_elastic_entity_stats,
        get_elastic_search_coverage,
        get_elastic_preservation_by_type,
        get_elastic_preservation_by_year,
        get_elastic_preservation_by_date,
)
from scholar.cat.forms import ReferenceMatchForm
from scholar.cat.graphics import (
        preservation_by_date_histogram,
        preservation_by_year_histogram,
)
from scholar.cat.entity_helpers import (
        generic_get_entity,
        generic_get_entity_revision,
        generic_get_editgroup_entity,
        editgroup_get_diffs,
)
from scholar.cat.tools.references import (
        enrich_inbound_refs,
        get_inbound_refs,
        enrich_outbound_refs,
        get_outbound_refs,
        RefHitsEnriched,
)
from scholar.cat.tools.transforms.access import (
        release_access_options,
)
from scholar.cat.tools.transforms.csl import (
        citeproc_csl,
        release_to_csl,
)
from scholar.cat.tools.transforms.entities import entity_to_dict
from scholar.config import GIT_REVISION, settings
from scholar.identifiers import clean_doi, clean_pmcid, clean_isbn13, clean_arxiv_id, clean_issn, clean_sha1, clean_sha256, clean_orcid

logger = logging.getLogger()

Ident: TypeAlias = Annotated[str, Path(min_length=26, max_length=26)]

routes = APIRouter()

# TODO port to basic Starlette
# I used FastAPI for the migration of fatcat.wiki into here because it's what
# Scholar was using. I didn't realize that Starlette would actually have been a
# better fit to begin with since Scholar is not intended, product-wise, to be
# an API. I would like to port both the scholar routes and the new cat routes
# to all be pure Starlette as I think it will make the code far more readable
# and maintainable.

# Because scholar's template loader is a special hacked one for i18n and
# because at this time we don't intend to add i18n to fatcat, I decided to make
# a separate template loader.
tmpls = Jinja2Templates(directory="src/scholar/templates/cat")
tmpls.env.globals["settings"] = settings

async def fcclient() -> DefaultApi:
    fc_conf = fcapi.Configuration()
    fc_conf.host = settings.FATCAT_API_HOST
    return DefaultApi(fcapi.ApiClient(fc_conf))

@routes.get("/", include_in_schema=False)
async def index(request: Request) -> Response:
    return tmpls.TemplateResponse(request, "index.html", {
        'git_revision': GIT_REVISION,
    })

@routes.post("/search", include_in_schema=False)
@routes.get("/search", include_in_schema=False)
async def search(request: Request, q: str | None = None) -> Response:
    if q is None:
        return RedirectResponse(request.url_for("release_search"), status_code=302)
    query = q.strip()

    if len(query.split()) != 1:
        # multi-term? must be a real search
        return RedirectResponse(
                request.url_for("release_search").include_query_params(
                    q=quote_plus(query),
                    generic=1),
                status_code=302)

    if clean_doi(query):
        return RedirectResponse(
                request.url_for("release_lookup").include_query_params(
                    doi=clean_doi(query)), status_code=302)

    if clean_pmcid(query):
        return RedirectResponse(
                request.url_for("release_lookup").include_query_params(
                    pmcid=clean_pmcid(query)), status_code=302)

    if clean_issn(query):
        return RedirectResponse(
                request.url_for("container_lookup").include_query_params(
                    issnl=clean_issn(query)), status_code=302)

    if clean_isbn13(query):
        return RedirectResponse(
                request.url_for("release_lookup").include_query_params(
                    isbn13=clean_isbn13(query)), status_code=302)

    if clean_arxiv_id(query):
        return RedirectResponse(
                request.url_for("release_lookup").include_query_params(
                    arxiv=clean_arxiv_id(query)), status_code=302)

    if clean_sha1(query):
        return RedirectResponse(
                request.url_for("file_lookup").include_query_params(
                    sha1=clean_sha1(query)), status_code=302)

    if clean_sha256(query):
        return RedirectResponse(
                request.url_for("file_lookup").include_query_params(
                    sha256=clean_sha256(query)), status_code=302)

    if clean_orcid(query):
        return RedirectResponse(
                request.url_for("creator_lookup").include_query_params(
                    orcid=clean_orcid(query)), status_code=302)

    return RedirectResponse(
            request.url_for("release_search").include_query_params(
                q=quote_plus(query),
                generic=1),
            status_code=302)

@routes.get("/creator/lookup")
async def creator_lookup(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        orcid:        str|None = None,
        wikidata_qid: str|None = None) -> Response:
    extid_types = [("orcid", orcid), ("wikidata_qid", wikidata_qid)]
    return generic_lookup(
            request, "creator", "creator_lookup.html",
            extid_types, lambda p: fcclient.lookup_creator(**p))


@routes.get("/file/lookup")
async def file_lookup(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        md5:      str|None = None,
        sha1:     str|None = None,
        sha256:   str|None = None) -> Response:
    extid_types = [("md5", md5), ("sha1", sha1), ("sha256", sha256)]
    return generic_lookup(
            request, "file", "file_lookup.html",
            extid_types, lambda p: fcclient.lookup_file(**p))

@routes.get("/container/lookup", include_in_schema=False)
async def container_lookup(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        issn:         str|None = None,
        issne:        str|None = None,
        issnp:        str|None = None,
        issnl:        str|None = None,
        wikidata_qid: str|None = None) -> Response:
    extid_types = [("issn", issn), ("issne", issne), ("issnp", issnp),
                   ("issnl", issnl), ("wikidata_qid", wikidata_qid)]
    return generic_lookup(request, "container", "container_lookup.html", extid_types,
                          lambda p: fcclient.lookup_container(**p))

def generic_lookup(request: Request,
                   entity_type: str,
                   tmpl: str,
                   extid_types: List[Tuple[str, str|None]],
                   lookup: Callable) -> Response:
    extid: str | None = None
    extidtype: str | None = None
    for et in extid_types:
        if et[1]:
            extid = et[1].strip()
            extidtype = et[0]
            break

    if extid is None:
        return tmpls.TemplateResponse(request, tmpl)

    try:
        resp = lookup({extidtype: extid})
    except ValueError:
        return tmpls.TemplateResponse(request, tmpl, {
            "lookup_key":   extidtype,
            "lookup_value": extid,
            "lookup_error": 400,
            }, status_code=400)
    except fcapi.ApiException as ae:
        if ae.status == 404 or ae.status == 400:
            return tmpls.TemplateResponse(request, tmpl, {
                "lookup_key":   extidtype,
                "lookup_value": extid,
                "lookup_error": ae.status,
                }, status_code=ae.status)
        else:
            raise ae

    return RedirectResponse(
            request.url_for(f"{entity_type}_view", ident=resp.ident), status_code=302)

@routes.get("/release/{ident}/save", include_in_schema=False)
async def release_save(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    release = fcclient.get_release(ident)
    return tmpls.TemplateResponse(request, "release_save.html", {'entity': release})

@routes.get("/release/lookup", include_in_schema=False)
async def release_lookup(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        doi:          str | None = None,
        wikidata_qid: str | None = None,
        pmid:         str | None = None,
        pmcid:        str | None = None,
        isbn13:       str | None = None,
        jstor:        str | None = None,
        arxiv:        str | None = None,
        core:         str | None = None,
        ark:          str | None = None,
        mag:          str | None = None,
        oai:          str | None = None,
        hdl:          str | None = None) -> Response:
    extid_types = [("doi", doi), ("wikidata_qid", wikidata_qid), ("pmid", pmid),
                   ("pmcid", pmcid), ("isbn13", isbn13), ("jstor", jstor), ("arxiv", arxiv),
                   ("core", core), ("ark", ark), ("mag", mag), ("oai", oai), ("hdl", hdl)]
    return generic_lookup(
            request, "release", "release_lookup.html", extid_types,
            lambda p: fcclient.lookup_release(**p))

@routes.post("/release/search", include_in_schema=False)
@routes.get("/release/search", include_in_schema=False)
async def release_search(
    request: Request,
    q: str | None = None,
    generic: int | None = None
) -> Response:
    ctx = {"git_revision": GIT_REVISION,
           "found": None,
           "query": ReleaseQuery(),
          }
    if q is None or len(q) == 0:
        return tmpls.TemplateResponse(request, "release_search.html", ctx)

    # if this is a "generic" query (eg, from front page or top-of page bar),
    # and the query is not all filters/paramters (aka, there is an actual
    # term/phrase in the query), then also try querying containers, and display
    # a "were you looking for" box with a single result
    container_found = None
    filter_only_query = True
    for p in q.split():
        if ":" not in p:
            filter_only_query = False
            break

    if generic and not filter_only_query:
        container_query = GenericQuery.from_args(request.query_params)
        container_query.limit = 1
        try:
            container_found = do_container_search(container_query)
        except Exception as e:
            logger.warn(f"container search failed: {e}")

    query = ReleaseQuery.from_args(request.query_params)
    try:
        found = do_release_search(query)
    except CatSearchError as cse:
        return tmpls.TemplateResponse(request, "release_search.html", ctx|{
            "es_error": cse,
            "query": query}, status_code=cse.status_code)

    return tmpls.TemplateResponse(request, "release_search.html", ctx|{
            "query": query,
            "found": found,
            "container_found": container_found})

@routes.get("/container/{ident}/history", include_in_schema=False)
async def container_history(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    entity = fcclient.get_container(ident)
    history = fcclient.get_container_history(ident)
    return tmpls.TemplateResponse(request, "entity_history.html", {
        'entity_type': 'container',
        'entity': entity,
        'history': history,
        })

@routes.get("/creator/{ident}/history", include_in_schema=False)
async def creator_history(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    entity = fcclient.get_creator(ident)
    history = fcclient.get_creator_history(ident)
    return tmpls.TemplateResponse(request, "entity_history.html", {
        'entity_type': 'creator',
        'entity': entity,
        'history': history,
        })

@routes.get("/file/{ident}/history", include_in_schema=False)
async def file_history(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    entity = fcclient.get_file(ident)
    history = fcclient.get_file_history(ident)
    return tmpls.TemplateResponse(request, "entity_history.html", {
        'entity_type': 'file',
        'entity': entity,
        'history': history,
        })

@routes.get("/fileset/{ident}/history", include_in_schema=False)
async def fileset_history(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    entity = fcclient.get_fileset(ident)
    history = fcclient.get_fileset_history(ident)
    return tmpls.TemplateResponse(request, "entity_history.html", {
        'entity_type': 'fileset',
        'entity': entity,
        'history': history,
        })

@routes.get("/webcapture/{ident}/history", include_in_schema=False)
async def webcapture_history(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    entity = fcclient.get_webcapture(ident)
    history = fcclient.get_webcapture_history(ident)
    return tmpls.TemplateResponse(request, "entity_history.html", {
        'entity_type': 'webcapture',
        'entity': entity,
        'history': history,
        })

@routes.get("/release/{ident}/history", include_in_schema=False)
async def release_history(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    entity = fcclient.get_release(ident)
    history = fcclient.get_release_history(ident)
    return tmpls.TemplateResponse(request, "entity_history.html", {
        'entity_type': 'release',
        'entity': entity,
        'history': history,
        })

@routes.get("/work/{ident}/history", include_in_schema=False)
async def work_history(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    entity = fcclient.get_work(ident)
    history = fcclient.get_work_history(ident)
    return tmpls.TemplateResponse(request, "entity_history.html", {
        'entity_type': 'work',
        'entity': entity,
        'history': history,
        })

def generic_entity_revision_view(
    request: Request,
    fcclient: fcapi.DefaultApi,
    entity_type: str,
    rev_id: UUID,
    tmpl: str) -> Response:
    entity = generic_get_entity_revision(fcclient, entity_type, rev_id)

    metadata = entity.to_dict()
    for k in GENERIC_ENTITY_FIELDS:
        metadata.pop(k)
    entity._metadata = metadata

    return tmpls.TemplateResponse(request, tmpl, {
        'entity_type': entity_type,
        'entity': entity,
        })

@routes.get("/container/rev/{rev_id}", include_in_schema=False)
async def container_revision_view(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'container',
                                        rev_id, 'container_view.html')

@routes.get("/container/rev/{rev_id}/metadata", include_in_schema=False)
async def container_revision_view_metadata(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'container',
                                        rev_id, 'entity_view_metadata.html')

@routes.get("/creator/rev/{rev_id}", include_in_schema=False)
async def creator_revision_view(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'creator',
                                        rev_id, 'creator_view.html')

@routes.get("/creator/rev/{rev_id}/metadata", include_in_schema=False)
async def creator_revision_view_metadata(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'creator',
                                        rev_id, 'entity_view_metadata.html')

@routes.get("/file/rev/{rev_id}", include_in_schema=False)
async def file_revision_view(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'file',
                                        rev_id, 'file_view.html')

@routes.get("/file/rev/{rev_id}/metadata", include_in_schema=False)
async def file_revision_view_metadata(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'file',
                                        rev_id, 'entity_view_metadata.html')

@routes.get("/webcapture/rev/{rev_id}", include_in_schema=False)
async def webcapture_revision_view(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'webcapture',
                                        rev_id, 'webcapture_view.html')

@routes.get("/webcapture/rev/{rev_id}/metadata", include_in_schema=False)
async def webcapture_revision_view_metadata(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'webcapture',
                                        rev_id, 'entity_view_metadata.html')
@routes.get("/release/rev/{rev_id}", include_in_schema=False)
async def release_revision_view(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'release',
                                        rev_id, 'release_view.html')

@routes.get("/release/rev/{rev_id}/metadata", include_in_schema=False)
async def release_revision_view_metadata(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'release',
                                        rev_id, 'entity_view_metadata.html')

@routes.get("/release/rev/{rev_id}/contribs", include_in_schema=False)
async def release_revision_view_contribs(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'release',
                                        rev_id, 'release_view_contribs.html')

@routes.get("/release/rev/{rev_id}/references", include_in_schema=False)
async def release_revision_view_references(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'release',
                                        rev_id, 'release_view_references.html')

@routes.get("/work/rev/{rev_id}", include_in_schema=False)
async def work_revision_view(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'work',
                                        rev_id, 'work_view.html')

@routes.get("/work/rev/{rev_id}/metadata", include_in_schema=False)
async def work_revision_view_metadata(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'work',
                                        rev_id, 'entity_view_metadata.html')

@routes.get("/fileset/rev/{rev_id}", include_in_schema=False)
async def fileset_revision_view(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'fileset',
                                        rev_id, 'fileset_view.html')

@routes.get("/fileset/rev/{rev_id}/metadata", include_in_schema=False)
async def fileset_revision_view_metadata(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        rev_id: UUID) -> Response:
    return generic_entity_revision_view(request, fcclient, 'fileset',
                                        rev_id, 'entity_view_metadata.html')

def browse_query(year: int|None, issue: str|None, volume: str|None) -> Tuple[str, List[str]]:
    # all of this logic is highly questionable to me but I'm just preserving
    # what was here and adding tests for it -nate
    query_string = ""
    query_sort = []
    vol = "!volume:*"
    iss = "!issue:*"
    def every(*xs: List[Any]) -> bool:
        return len([x for x in xs if x is not None]) == len(xs)
    if every(year, issue, volume):
        # year, volume, issue specified; browse-by-page
        if  volume != "":
            vol = f'volume:"{volume}"'
        if issue != "":
            iss = f'issue:"{issue}"'
        query_string = f"year:{year} {vol} {iss}"
        query_sort = ["first_page", "pages", "release_date"]
    elif every(year, volume):
        # year, volume specified (no issue); browse-by-page
        if  volume != "":
            vol = f'volume:"{volume}"'
        query_string = f"year:{year} {vol}"
        query_sort = ["issue", "first_page", "pages", "release_date"]
    elif year is not None:
        # year specified, not anything else; browse-by-date
        query_string = f"year:{year}"
        query_sort = ["release_date"]
    elif volume is not None:
        if  volume != "":
            vol = f'volume:"{volume}"'
        # volume specified, not anything else; browse-by-page
        query_string = vol
        query_sort = ["issue", "first_page", "pages", "release_date"]
    return (query_string, query_sort)

def test_browse_query() -> None:
    @dataclass
    class case:
        name: str
        args: list[str|None]
        expected: tuple[str, list[str]]

    # year, issue, volume
    cases = [case(name="all none",
                  args=[None, None, None],
                  expected=("", [])),
             case(name="just year",
                  args=[1969, None, None],
                  expected=("year:1969", ["release_date"])),
             case(name="just volume",
                  args=[None, None, "6"],
                  expected=('volume:"6"', ["issue", "first_page", "pages", "release_date"])),
             case(name="just volume but it is blank",
                  args=[None, None, ""],
                  expected=('!volume:*', ["issue", "first_page", "pages", "release_date"])),
             case(name="year and blanks",
                  args=[1969, "", ""],
                  expected=("year:1969 !volume:* !issue:*", ["first_page", "pages", "release_date"])),
             case(args=[1969, None, ""],
                  name="year, empty volume, no issue",
                  expected=("year:1969 !volume:*", ["issue", "first_page", "pages", "release_date"])),
             case(args=[1969, "", None],
                  name="year, empty issue, no volume",
                  expected=("year:1969", ["release_date"])),
             case(args=[1969, "13", "6"],
                  name="all there",
                  expected=('year:1969 volume:"6" issue:"13"', ["first_page", "pages", "release_date"])),
            ]
    for c in cases:
        result = browse_query(*c.args)
        if result[0] == "":
            assert result == c.expected, c.name
        else:
            assert result[0] == c.expected[0], c.name
            assert result[1] == c.expected[1], c.name


@routes.get("/container/{ident}/browse", include_in_schema=False)
async def container_view_browse(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident,
        year:     int|None = None,
        volume:   str|None = None,
        issue:    str|None = None) -> Response:
    entity = generic_get_entity(fcclient, "container", ident)

    if entity.state == "redirect":
        return RedirectResponse(
                request.url_for("container_view",
                                ident=entity.redirect), status_code=302)
    elif entity.state == "deleted":
        return tmpls.TemplateResponse(request, "deleted_entity.html", {
            "entity_type": "container",
            "entity": entity})

    q = browse_query(year, issue, volume)
    if q is None:
        entity._browse_year_volume_issue = get_elastic_container_browse_year_volume_issue(
            entity.ident
        )
        return tmpls.TemplateResponse(request, "container_view_browse.html", {
            'entity_type': 'container',
            'entity': entity,
            'volume': volume,
            'issue': issue,
            'year': year,
            # 'editgroup_id: None
            })
    query_string, query_sort = q

    query = ReleaseQuery(
        q=query_string,
        limit=300,
        offset=0,
        container_id=ident,
        fulltext_only=False,
        recent=False,
        exclude_stubs=True,
        sort=query_sort,
    )

    try:
        found = do_release_search(query)
    except CatSearchError as fse:
        return tmpls.TemplateResponse(request, "container_view_search.html", {
            'query': query,
            'es_error': fse,
            'entity_type': 'container',
            'entity': entity,
            }, status_code=fse.status_code)

    # HACK: re-sort by first page *numerically*
    if found.results and query_sort and "first_page" in query_sort:
        for doc in found.results:
            if doc.get("first_page") and doc["first_page"].isdigit():
                doc["first_page"] = int(doc["first_page"])
        found.results = sorted(found.results, key=lambda d: d.get("first_page") or 99999999)

    return tmpls.TemplateResponse(request, "container_view_browse.html", {
            'query': query,
            'releases_found': found,
            'entity_type': 'container',
            'entity': entity,
            'volume': volume,
            'issue': issue,
            'year': year,
        })

# TODO self hosted statping for scholar
# TODO sitemap. deprioritizing since the existing one is already 2 years out of date.
# TODO markdown filter for annotations. deprioritizing because there are just not many annotations.

@routes.get("/about", include_in_schema=False)
async def page_about(request: Request) -> Response:
    return tmpls.TemplateResponse(request, "about.html")

# settings ported from cors.py in fatcat
async def cors(request: Request, response: Response) -> None:
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS, GET'
    response.headers['Access-Control-Allow-Headers'] = 'ACCESS-CONTROL-ALLOW-ORIGIN, CONTENT-TYPE'
    response.headers['Access-Control-Max-Age'] = '21600'

@routes.options("/release/{ident}/refs-out.json",
                response_model=None, include_in_schema=False)
@routes.get("/release/{ident}/refs-out.json", response_model=None, include_in_schema=False)
async def release_view_refs_outbound_json(
        request:  Request,
        response: Response,
        _cors:    Annotated[None, Depends(cors)],
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> RefHitsEnriched|Response:
    if request.method == 'OPTIONS':
        response.status_code = 200
        return response
    return _refs_web("out", fcclient=fcclient, release_ident=ident)

@routes.options("/release/{ident}/refs-in.json", response_model=None, include_in_schema=False)
@routes.get("/release/{ident}/refs-in.json", response_model=None, include_in_schema=False)
async def release_view_refs_inbound_json(
        request:  Request,
        response: Response,
        _cors:    Annotated[None, Depends(cors)],
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> RefHitsEnriched|Response:
    if request.method == 'OPTIONS':
        response.status_code = 200
        return response
    return _refs_web("in", fcclient=fcclient, release_ident=ident)

@routes.options("/openlibrary/OL{id_num}W/refs-in.json",
            response_model=None, include_in_schema=False)
@routes.get("/openlibrary/OL{id_num}W/refs-in.json",
            response_model=None, include_in_schema=False)
async def openlibrary_view_refs_inbound_json(
        request:   Request,
        response:  Response,
        _cors:     Annotated[None, Depends(cors)],
        fcclient:  Annotated[fcapi.DefaultApi, Depends(fcclient)],
        id_num:    Annotated[int, Path(ge=0)],
        ) -> RefHitsEnriched|Response:
    if request.method == 'OPTIONS':
        response.status_code = 200
        return response
    return _refs_web("in", fcclient=fcclient, openlibrary_id=f"OL{id_num}W")

@routes.options("/wikipedia/{wiki_lang}:{wiki_article}/refs-out.json",
            response_model=None, include_in_schema=False)
@routes.get("/wikipedia/{wiki_lang}:{wiki_article}/refs-out.json",
            response_model=None, include_in_schema=False)
async def wikipedia_view_refs_outbound_json(
        request:      Request,
        response:     Response,
        _cors:        Annotated[None, Depends(cors)],
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        wiki_lang:    Annotated[str, Path(length=2)],
        wiki_article: str,
) -> RefHitsEnriched|Response:
    if request.method == 'OPTIONS':
        response.status_code = 200
        return response
    wiki_article = wiki_article.replace("_", " ")
    wikipedia_article = wiki_lang + ":" + wiki_article
    return _refs_web("out",
                     fcclient=fcclient,
                     wikipedia_article=wikipedia_article)

@routes.options("/reference/match.json", response_model=None, include_in_schema=False)
@routes.get("/reference/match.json", response_model=None, include_in_schema=False)
async def reference_match_json(
        request:      Request,
        response:     Response,
        _cors:        Annotated[None, Depends(cors)],
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ) -> List[Any]|dict|Response:
    if request.method == "OPTIONS":
        response.status_code = 200
        return response

    form = await ReferenceMatchForm.from_formdata(request=request, formdata=request.query_params)
    if not await form.validate():
        response.status_code = 400
        return form.errors

    if form.submit_type.data != "match":
        raise NotImplementedError()

    es_backend = settings.ELASTICSEARCH_FATCAT_BASE
    es_client = elasticsearch.Elasticsearch(es_backend)

    matches = close_fuzzy_biblio_matches(es_client=es_client,
                                         biblio=form.data, match_limit=10) or []
    resp = []
    for m in matches:
        # expand releases more completely
        m.release = fcclient.get_release(
            m.release.ident,
            expand="container,files,filesets,webcaptures",
            hide="abstract,refs",
        )
        # hack in access options
        m.access_options = release_access_options(m.release)

        # and manually convert to dict (for jsonify)
        info = m.__dict__
        info["release"] = entity_to_dict(m.release)
        info["access_options"] = [o.dict() for o in m.access_options]
        resp.append(info)
    return resp

@routes.get("/changelog", include_in_schema=False)
async def changelog_view(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)]) -> Response:
    entries = fcclient.get_changelog()
    return tmpls.TemplateResponse(request, "changelog.html", {'entries': entries})

@routes.get("/changelog/{index}", include_in_schema=False)
async def changelog_entry_view(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        index: int) -> Response:
    entry = fcclient.get_changelog_entry(index)
    entry.editgroup.editor = fcclient.get_editor(entry.editgroup.editor_id)
    entry.editgroup.annotations = fcclient.get_editgroup_annotations(
        entry.editgroup_id, expand="editors"
    )
    return tmpls.TemplateResponse(request, "changelog_view.html", {
        'entry': entry,
        'editgroup': entry.editgroup})

@routes.get("/stats", include_in_schema=False)
async def stats_page(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ) -> Response:
    stats = get_elastic_entity_stats()
    stats.update(get_changelog_stats(fcclient))
    return tmpls.TemplateResponse(request, "stats.html", {'stats': stats})

def get_changelog_stats(fcclient: fcapi.DefaultApi) -> Dict[str, Any]:
    stats = {}
    latest_changelog = fcclient.get_changelog(limit=1)[0]
    stats["changelog"] = {
        "latest": {
            "index": latest_changelog.index,
            "timestamp": latest_changelog.timestamp.isoformat(),
        }
    }
    return stats

@routes.get("/coverage/search", include_in_schema=False)
@routes.post("/coverage/search", include_in_schema=False)
async def coverage_search(request: Request,
                          q: str|None = None,
                          ) -> Response:

    ctx = {'query': ReleaseQuery(),
           'coverage_stats': None,
           'coverage_type_preservation': None,
           'year_histogram_svg': None,
           'date_histogram_svg': None}

    if q is None:
        return tmpls.TemplateResponse(request, "coverage_search.html", ctx)

    query = ReleaseQuery(q=q)
    ctx['query'] = query
    try:
        coverage_stats = get_elastic_search_coverage(query)
    except CatSearchError as fse:
        return tmpls.TemplateResponse(request, "coverage_search.html",
                                      ctx|{'es_error':fse},
                                      status_code=fse.status_code)
    year_histogram_svg = None
    date_histogram_svg = None
    coverage_type_preservation = None
    if coverage_stats["total"] > 1:
        coverage_type_preservation = get_elastic_preservation_by_type(query)
        if query.recent:
            date_histogram = get_elastic_preservation_by_date(query)
            date_histogram_svg = preservation_by_date_histogram(
                date_histogram).render_data_uri()
        else:
            year_histogram = get_elastic_preservation_by_year(query)
            year_histogram_svg = preservation_by_year_histogram(
                year_histogram).render_data_uri()
    return tmpls.TemplateResponse(request, "coverage_search.html", ctx|{
        'coverage_stats': coverage_stats,
        'coverage_type_preservation': coverage_type_preservation,
        'year_histogram_svg': year_histogram_svg,
        'date_histogram_svg': date_histogram_svg,
        })

GENERIC_ENTITY_FIELDS = ["extra", "edit_extra", "revision", "redirect", "state", "ident"]

def generic_entity_view(request: Request, fcclient: fcapi.DefaultApi, entity_type: str, ident: str, tmpl: str) -> Response:
    entity = generic_get_entity(fcclient, entity_type, ident)

    if entity.state == "redirect":
        return RedirectResponse(request.url_for(f"{entity_type}_view", ident=entity.redirect), status_code=302)
    elif entity.state == "deleted":
        return tmpls.TemplateResponse(request, "deleted_entity.html", {
            "entity_type": entity_type,
            "entity": entity})

    metadata = entity.to_dict()
    for k in GENERIC_ENTITY_FIELDS:
        metadata.pop(k)
    entity._metadata = metadata

    if tmpl == "container_view.html":
        entity._stats = get_elastic_container_stats(entity.ident, issnl=entity.issnl)
        entity._random_releases = get_elastic_container_random_releases(entity.ident)

    if tmpl == "container_view_coverage.html":
        entity._stats = get_elastic_container_stats(entity.ident, issnl=entity.issnl)
        entity._type_preservation = get_elastic_preservation_by_type(
            ReleaseQuery(container_id=ident),
        )
    return tmpls.TemplateResponse(request, tmpl, {
        "entity_type": entity_type,
        "entity": entity,
        })

@routes.get("/container/search", include_in_schema=False)
async def container_search(request: Request,
                           q: str|None = None) -> Response:
    ctx = {'query': GenericQuery(),
           'found': None,}

    if q is None:
        return tmpls.TemplateResponse(request, "container_search.html", ctx)

    query = GenericQuery(q=q)
    ctx['query'] = query
    try:
        found = do_container_search(query)
    except CatSearchError as fse:
        return tmpls.TemplateResponse(request, "container_search.html",
                                ctx|{'es_error': fse},
                                status_code=fse.status_code)
    return tmpls.TemplateResponse(request, "container_search.html", ctx|{'found':found})

@routes.get("/container/{ident}/search", include_in_schema=False)
async def container_view_search(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident,
        q:        str|None = None) -> Response:
    entity = generic_get_entity(fcclient, "container", ident)

    ctx = {'entity_type': 'container',
           'entity': entity,
           'query': ReleaseQuery(),}

    if entity.state == "redirect":
        return RedirectResponse(
                request.url_for("container_view", ident=entity.redirect),
                status_code=302)
    elif entity.state == "deleted":
        return tmpls.TemplateResponse(request, "deleted_entity.html", ctx)
    if q is None:
        return tmpls.TemplateResponse(request, "container_view_search.html", ctx)

    query = ReleaseQuery(q=q, container_id=ident)
    ctx.update({'query': query})
    try:
        found = do_release_search(query)
    except CatSearchError as fse:
        return tmpls.TemplateResponse(request, "container_view_search.html",
                                      ctx|{'es_error': fse},
                                      status_code=fse.status_code)

    return tmpls.TemplateResponse(request, "container_view_search.html",
                                  ctx|{'found': found})

@routes.get("/container/{ident}/coverage", include_in_schema=False)
async def container_view_coverage(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    # note: there is a special hack to add entity._type_preservation for this endpoint
    return generic_entity_view(request, fcclient, "container", ident, "container_view_coverage.html")

@routes.get("/container_{ident}", include_in_schema=False)
async def container_underscore_view(
        request:  Request,
        ident:    Ident) -> Response:
    return RedirectResponse(request.url_for("container_view", ident=ident),
                            status_code=302)

@routes.get("/file_{ident}", include_in_schema=False)
async def file_underscore_view(
        request:  Request,
        ident:    Ident) -> Response:
    return RedirectResponse(request.url_for("file_view", ident=ident),
                            status_code=302)

@routes.get("/container/{ident}/metadata", include_in_schema=False)
async def container_view_metadata(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "container", ident, "entity_view_metadata.html")

@routes.get("/creator_{ident}", include_in_schema=False)
async def creator_underscore_view(
        request:  Request,
        ident:    Ident) -> Response:
    return RedirectResponse(request.url_for("creator_view", ident=ident), status_code=302)

@routes.get("/creator/{ident}/metadata", include_in_schema=False)
async def creator_view_metadata(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "creator", ident, "entity_view_metadata.html")

@routes.get("/file/{ident}/metadata", include_in_schema=False)
async def file_view_metadata(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "file", ident, "entity_view_metadata.html")

@routes.get("/release_{ident}", include_in_schema=False)
async def release_underscore_view(
        request:  Request,
        ident:    Ident) -> Response:
    return RedirectResponse(request.url_for("release_view", ident=ident), status_code=302)

@routes.get("/release/{ident}/contribs", include_in_schema=False)
async def release_view_contribs(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "release",
                               ident, "release_view_contribs.html")

@routes.get("/release/{ident}/references", include_in_schema=False)
async def release_view_references(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "release",
                               ident, "release_view_references.html")

@routes.get("/webcapture/{ident}", include_in_schema=False)
async def webcapture_view(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "webcapture", ident, "webcapture_view.html")

@routes.get("/webcapture_{ident}", include_in_schema=False)
async def webcapture_underscore_view(
        request:  Request,
        ident:    Ident) -> Response:
    return RedirectResponse(request.url_for("webcapture_view", ident=ident), status_code=302)

@routes.get("/webcapture/{ident}/metadata", include_in_schema=False)
async def webcapture_view_metadata(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "webcapture", ident, "entity_view_metadata.html")

@routes.get("/work/{ident}/metadata", include_in_schema=False)
async def work_view_metadata(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "work", ident, "entity_view_metadata.html")

@routes.get("/work_{ident}", include_in_schema=False)
async def work_underscore_view(
        request:  Request,
        ident:    Ident) -> Response:
    return RedirectResponse(request.url_for("work_view", ident=ident), status_code=302)

@routes.get("/work/{ident}", include_in_schema=False)
async def work_view(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "work", ident, "work_view.html")

@routes.get("/release/{ident}.bib", include_in_schema=False)
async def release_bibtex(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    entity = fcclient.get_release(ident)
    try:
        csl = release_to_csl(entity)
    except ValueError as e:
        # "handle" the missing author/surname path, so we don't get exception
        # reports about it. these are not linked to, only show up from bots.
        return Response(status_code=400, content=e, media_type="text/plain")
    bibtex = citeproc_csl(csl, "bibtex")
    return Response(content=bibtex, media_type="text/plain")

@routes.get("/release/{ident}/citeproc", include_in_schema=False)
async def release_citeproc(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident,
        style:    str = "harvard1") -> Response:
    # There was a way to have citeproc_csl generate html but as far as I could
    # tell it was unused. I ran into some encoding issues and decided to just
    # leave it out. It's not linked to from anywhere and not used in any
    # scripts.
    entity = fcclient.get_release(ident)
    try:
        csl = release_to_csl(entity)
    except ValueError as e:
        # "handle" the missing author/surname path, so we don't get exception
        # reports about it. these are not linked to, only show up from bots.
        return Response(status_code=400, content=e, media_type="text/plain")
    try:
        cite = citeproc_csl(csl, style)
    except citeproc_styles.StyleNotFoundError as e:
        # "handle" the missing author/surname path, so we don't get exception
        # reports about it. these are not linked to, only show up from bots.
        return Response(status_code=400, content=str(e), media_type="text/plain")
    if style == "csl-json":
        return Response(content=cite, media_type="application/json")
    else:
        return Response(content=cite, media_type="text/plain")

@routes.get("/release/{ident}/metadata", include_in_schema=False)
async def release_view_metadata(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "release", ident, "entity_view_metadata.html")

@routes.get("/release/{ident}", include_in_schema=False)
async def release_view(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident: Ident) -> Response:
    return generic_entity_view(request, fcclient, "release", ident, "release_view.html")

@routes.get("/creator/{ident}", include_in_schema=False)
async def creator_view(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "creator", ident, "creator_view.html")


@routes.get("/file/{ident}", include_in_schema=False)
async def file_view(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "file", ident, "file_view.html")


@routes.get("/container/{ident}", include_in_schema=False)
async def container_view(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "container", ident, "container_view.html")

@routes.get("/fileset_{ident}")
async def fileset_underscore_view(request: Request,
                                  ident: str = Path(..., min_length=1, max_length=30)) -> Response:
    return RedirectResponse(request.url_for("fileset_view", ident=ident), status_code=302)

@routes.get("/fileset/{ident}/metadata")
async def fileset_view_metadata(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "fileset", ident, "entity_view_metadata.html")

@routes.get("/fileset/{ident}")
async def fileset_view(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    return generic_entity_view(request, fcclient, "fileset", ident, "fileset_view.html")

def generic_editgroup_entity_view(
    request: Request,
    fcclient: fcapi.DefaultApi,
    editgroup_id: str|None,
    entity_type: str,
    ident: str,
    view_template: str) -> Response:
    editgroup = fcclient.get_editgroup(editgroup_id)

    entity, edit = generic_get_editgroup_entity(fcclient, editgroup, entity_type, ident)

    ctx = {'request': request,
           'entity': entity,
           'entity_type': entity_type,
           'editgroup': editgroup,
          }

    if entity.revision is None or entity.state == "deleted":
        return tmpls.TemplateResponse(request, "deleted_entity.html", ctx)

    metadata = entity.to_dict()
    for k in GENERIC_ENTITY_FIELDS:
        metadata.pop(k)
    entity._metadata = metadata

    return tmpls.TemplateResponse(request, view_template, ctx)

@routes.get("/editgroup/{editgroup_id}/container/{ident}", include_in_schema=False)
async def container_editgroup_view(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'container',
            ident, 'container_view.html')

@routes.get("/editgroup/{editgroup_id}/container/{ident}/metadata", include_in_schema=False)
async def container_editgroup_view_metadata(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'container',
            ident, 'entity_view_metadata.html')

@routes.get("/editgroup/{editgroup_id}/creator/{ident}", include_in_schema=False)
async def creator_editgroup_view(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'creator',
            ident, 'creator_view.html')

@routes.get("/editgroup/{editgroup_id}/creator/{ident}/metadata", include_in_schema=False)
async def creator_editgroup_view_metadata(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'creator',
            ident, 'entity_view_metadata.html')

@routes.get("/editgroup/{editgroup_id}/file/{ident}", include_in_schema=False)
async def file_editgroup_view(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'file',
            ident, 'file_view.html')

@routes.get("/editgroup/{editgroup_id}/file/{ident}/metadata", include_in_schema=False)
async def file_editgroup_view_metadata(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'file',
            ident, 'entity_view_metadata.html')

@routes.get("/editgroup/{editgroup_id}/fileset/{ident}", include_in_schema=False)
async def fileset_editgroup_view(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'fileset',
            ident, 'fileset_view.html')

@routes.get("/editgroup/{editgroup_id}/fileset/{ident}/metadata", include_in_schema=False)
async def fileset_editgroup_view_metadata(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'fileset',
            ident, 'entity_view_metadata.html')

@routes.get("/editgroup/{editgroup_id}/webcapture/{ident}", include_in_schema=False)
async def webcapture_editgroup_view(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'webcapture',
            ident, 'webcapture_view.html')

@routes.get("/editgroup/{editgroup_id}/webcapture/{ident}/metadata", include_in_schema=False)
async def webcapture_editgroup_view_metadata(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'webcapture',
            ident, 'entity_view_metadata.html')

@routes.get("/editgroup/{editgroup_id}/release/{ident}", include_in_schema=False)
async def release_editgroup_view(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'release',
            ident, 'release_view.html')

@routes.get("/editgroup/{editgroup_id}/release/{ident}/metadata", include_in_schema=False)
async def release_editgroup_view_metadata(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'release',
            ident, 'entity_view_metadata.html')

@routes.get("/editgroup/{editgroup_id}/release/{ident}/contribs", include_in_schema=False)
async def release_editgroup_view_contribs(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'release',
            ident, 'release_view_contribs.html')

@routes.get("/editgroup/{editgroup_id}/release/{ident}/references", include_in_schema=False)
async def release_editgroup_view_references(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'release',
            ident, 'release_view_references.html')

@routes.get("/editgroup/{editgroup_id}/work/{ident}", include_in_schema=False)
async def work_editgroup_view(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'work',
            ident, 'work_view.html')

@routes.get("/editgroup/{editgroup_id}/work/{ident}/metadata", include_in_schema=False)
async def work_editgroup_view_metadata(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        editgroup_id: str,
        ident:        Ident) -> Response:
    return generic_editgroup_entity_view(
            request, fcclient, editgroup_id, 'work',
            ident, 'entity_view_metadata.html')

@routes.get("/editgroup/{ident}", include_in_schema=False)
async def editgroup_view(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    eg = fcclient.get_editgroup(ident)
    eg.editor = fcclient.get_editor(eg.editor_id)
    eg.annotations = fcclient.get_editgroup_annotations(
            eg.editgroup_id, expand="editors")
    return tmpls.TemplateResponse(request, "editgroup_view.html", {'editgroup': eg})

@routes.get("/editgroup_{ident}", include_in_schema=False)
async def editgroup_underscore_view(
        request: Request,
        ident:   Ident) -> Response:
    return RedirectResponse(request.url_for("editgroup_view", ident=ident),
                            status_code=302)

@routes.get("/editgroup/{ident}/diff", include_in_schema=False)
async def editgroup_diff_view(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    eg = fcclient.get_editgroup(ident)
    eg.editor = fcclient.get_editor(eg.editor_id)
    eg.annotations = fcclient.get_editgroup_annotations(
            eg.editgroup_id, expand="editors")
    diffs = editgroup_get_diffs(fcclient, eg)
    return tmpls.TemplateResponse(request, "editgroup_diff.html", {
        'editgroup': eg,
        'editgroup_diffs': diffs,
        })

@routes.get("/editor/{ident}", include_in_schema=False)
async def editor_view(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    entity = fcclient.get_editor(ident)
    return tmpls.TemplateResponse(request, "editor_view.html", {'editor': entity})

@routes.get("/editor_{ident}", include_in_schema=False)
async def editor_underscore_view(
        request: Request,
        ident:   Ident) -> Response:
    return RedirectResponse(request.url_for("editor_view", ident=ident),
                            status_code=302)

@routes.get("/editor/{ident}/editgroups", include_in_schema=False)
async def editor_editgroups(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    editor = fcclient.get_editor(ident)
    editgroups = fcclient.get_editor_editgroups(ident, limit=50)
    # cheaper than API-side expand?
    for eg in editgroups:
        eg.editor = editor
    return tmpls.TemplateResponse(request, "editor_editgroups.html", {
        'editor': editor,
        'editgroups': editgroups,
        })

@routes.get("/editor/{ident}/annotations", include_in_schema=False)
async def editor_annotations(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    editor = fcclient.get_editor(ident)
    annotations = fcclient.get_editor_annotations(ident, limit=50)
    return tmpls.TemplateResponse(request, "editor_annotations.html", {
        'editor': editor,
        'annotations': annotations,
        })

@routes.get("/u/{username}", include_in_schema=False)
async def editor_username_redirect(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        username: Annotated[str, Path(min_length=1, max_length=100)],
) -> Response:
    editor = fcclient.lookup_editor(username=username)
    return RedirectResponse(
        request.url_for("editor_view", ident=editor.editor_id),
        status_code=302)

def _refs_web(
    direction:         str,
    fcclient:          fcapi.DefaultApi,
    offset:            int = 0,
    limit:             int = 30,
    release_ident:     str|None = None,
    work_ident:        str|None = None,
    openlibrary_id:    str|None = None,
    wikipedia_article: str|None = None,
) -> RefHitsEnriched:
    offset = max(0, offset)
    limit = max(0, min(limit, 100))

    es_backend = settings.ELASTICSEARCH_FATCAT_BASE
    es_client = elasticsearch.Elasticsearch(es_backend)

    if direction == "in":
        hits = get_inbound_refs(
            es_client,
            release_ident=release_ident,
            work_ident=work_ident,
            openlibrary_work=openlibrary_id,
            offset=offset,
            limit=limit,
        )
        enriched_hits = hits.as_enriched(
            enrich_inbound_refs(
                hits.result_refs,
                fcclient=fcclient,
                expand="container,files,webcaptures",
            )
        )
    elif direction == "out":
        hits = get_outbound_refs(
            release_ident=release_ident,
            wikipedia_article=wikipedia_article,
            work_ident=work_ident,
            es_client=es_client,
            offset=offset,
            limit=limit,
        )
        enriched_hits = hits.as_enriched(
            enrich_outbound_refs(
                hits.result_refs,
                fcclient=fcclient,
                expand="container,files,webcaptures",
            )
        )
    else:
        raise ValueError()
    return enriched_hits

@routes.get("/release/{ident}/refs-in", include_in_schema=False)
async def release_view_refs_inbound(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    release = generic_get_entity(fcclient, "release", ident)
    hits = _refs_web("in", fcclient=fcclient, release_ident=ident)
    return tmpls.TemplateResponse(request, "release_view_fuzzy_refs.html", {
        'direction': 'in',
        'entity': release,
        'hits': hits,
        })

@routes.get("/release/{ident}/refs-out", include_in_schema=False)
async def release_view_refs_outbound(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        ident:    Ident) -> Response:
    release = generic_get_entity(fcclient, "release", ident)
    hits = _refs_web("out", fcclient=fcclient, release_ident=ident)
    return tmpls.TemplateResponse(request, "release_view_fuzzy_refs.html", {
        'direction': 'out',
        'entity': release,
        'hits': hits,
        })

@routes.get("/openlibrary/OL{id_num}W/refs-in", include_in_schema=False)
async def openlibrary_view_refs_inbound(
        request:  Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
        id_num:   Annotated[int, Path(ge=0)],
) -> Response:
    openlibrary_id = f"OL{id_num}W"
    hits = _refs_web("in", fcclient=fcclient, openlibrary_id=openlibrary_id)
    return tmpls.TemplateResponse(request, "openlibrary_view_fuzzy_refs.html", {
        'openlibrary_id': openlibrary_id,
        'direction': 'in',
        'hits': hits,
        })

@routes.get("/wikipedia/{wiki_lang}:{wiki_article}/refs-out", include_in_schema=False)
async def wikipedia_view_refs_outbound(
        request:      Request,
        fcclient:     Annotated[fcapi.DefaultApi, Depends(fcclient)],
        wiki_lang:    Annotated[str, Path(min_length=2, max_length=2)],
        wiki_article: str,
) -> Response:
    wiki_url = f"https://{wiki_lang}.wikipedia.org/wiki/{wiki_article}"
    wiki_article = wiki_article.replace("_", " ")
    wikipedia_article = wiki_lang + ":" + wiki_article
    hits = _refs_web("out",
                     fcclient=fcclient,
                     wikipedia_article=wikipedia_article)
    return tmpls.TemplateResponse(request, "wikipedia_view_fuzzy_refs.html", {
                'wiki_article': wiki_article,
                'wiki_lang': wiki_lang,
                'wiki_url': wiki_url,
                'direction': "out",
                'hits': hits,
                })

@routes.get("/reference/match", include_in_schema=False)
@routes.post("/reference/match", include_in_schema=False)
async def reference_match(
        request: Request,
        fcclient: Annotated[fcapi.DefaultApi, Depends(fcclient)],
) -> Response:
    grobid_status = None
    grobid_dict = None

    form = await ReferenceMatchForm.from_formdata(request)

    ctx = {'form': form}

    if request.method == 'GET':
        return tmpls.TemplateResponse(request, "reference_match.html", ctx)

    if not await form.validate_on_submit():
        return tmpls.TemplateResponse(request, "reference_match.html", ctx,
                                      status_code=400)

    es_backend = settings.ELASTICSEARCH_FATCAT_BASE
    es_client = elasticsearch.Elasticsearch(es_backend)

    if form.submit_type.data == "parse":
        resp_xml = grobid_api_process_citation(form.raw_citation.data)
        if not resp_xml:
            grobid_status = "failed"
            return tmpls.TemplateResponse(request, "reference_match.html", ctx|{
                'grobid_status': grobid_status,
                }, status_code=400)
        grobid_dict = transform_grobid_ref_xml(resp_xml)
        if not grobid_dict:
            grobid_status = "empty"
            return tmpls.TemplateResponse(request, "reference_match.html", ctx|{
                'grobid_status': grobid_status,
                })
        release_stub = grobid_ref_to_release(grobid_dict)
        # remove empty values from GROBID parsed dict
        grobid_dict = {k: v for k, v in grobid_dict.items() if v is not None}
        ctx['form'] = ReferenceMatchForm.from_grobid_parse(request,
                                                    grobid_dict,
                                                    form.raw_citation.data)
        grobid_status = "success"
        matches = (
            close_fuzzy_release_matches(
                es_client=es_client, release=release_stub, match_limit=10
            )
            or []
        )
    elif form.submit_type.data == "match":
        matches = (
            close_fuzzy_biblio_matches(
                es_client=es_client, biblio=form.data, match_limit=10
            )
            or []
        )
    else:
        raise NotImplementedError()

    for m in matches:
        # expand releases more completely
        m.release = fcclient.get_release(
            m.release.ident,
            expand="container,files,filesets,webcaptures",
            hide="abstract,refs",
        )
        # hack in access options
        m.access_options = release_access_options(m.release)

    return tmpls.TemplateResponse(request, "reference_match.html", ctx|{
        'grobid_dict': grobid_dict,
        'grobid_status': grobid_status,
        'matches': matches,
        })
