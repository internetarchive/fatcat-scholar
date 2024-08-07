"""
This contains the FastAPI web application and RESTful API.

So far there are few endpoints, so we just put them all here!
"""

import datetime
import json
import logging
import urllib.parse
from typing import Any, Dict, List, Optional

import fastapi_rss
import fatcat_openapi_client as fcapi
import sentry_sdk
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path, Request, Response
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette_prometheus import PrometheusMiddleware, metrics
from starlette import templating

from scholar.config import GIT_REVISION, I18N_LANG_OPTIONS, settings
from scholar.schema import ScholarDoc
from scholar.search import (
    FulltextHits,
    FulltextQuery,
    es_scholar_index_alive,
    get_es_scholar_doc,
    process_query,
)
from scholar.web_hacks import i18n_templates, parse_accept_lang
from scholar.fatcat.web import routes as fc_web_routes
from scholar.fatcat.web import tmpls as fc_tmpls
from scholar.fatcat.api import routes as fc_api_routes

logger = logging.getLogger()


class LangPrefix:
    """
    Looks for either a two-character URL path prefix, or an Accept-Language
    HTTP header, to determine which translation of the site to display.

    A URL path-prefix takes precedence, then an Accept-Language header is
    considered, and finally a configurable default is used. Any path prefix is
    stored as a context variable, so that URLs can be re-written in templates
    to include the prefix.
    """

    def __init__(self, request: Request):
        self.prefix: str = ""
        self.code: str = settings.I18N_LANG_DEFAULT
        # first try to parse a language code from header
        try:
            accept_code = parse_accept_lang(
                request.headers.get("accept-language", ""),
                I18N_LANG_OPTIONS,
            )
            if accept_code:
                self.code = accept_code
        except Exception:
            pass

        # then override this with any language code in URL
        for lang_option in I18N_LANG_OPTIONS:
            if request.url.path.startswith(f"/{lang_option}/"):
                self.prefix = f"/{lang_option}"
                self.code = lang_option
                break
        sentry_sdk.set_tag("locale", self.code)

web = APIRouter()

@web.get("/_health", operation_id="get_health", include_in_schema=False)
def health_get() -> Any:
    """
    Checks that connection back to elasticsearch index is working.
    """
    if not es_scholar_index_alive():
        raise HTTPException(status_code=503)
    return Response()


@web.head("/_health", include_in_schema=False)
def health_head() -> Any:
    return health_get()

@web.get("/", include_in_schema=False)
def web_home(
    request: Request,
    lang: LangPrefix = Depends(LangPrefix),
) -> Any:
    return i18n_templates(lang.code).TemplateResponse(
        "home.html",
        {"request": request, "locale": lang.code, "lang_prefix": lang.prefix},
    )


@web.get("/about", include_in_schema=False)
def web_about(request: Request, lang: LangPrefix = Depends(LangPrefix)) -> Any:
    return i18n_templates(lang.code).TemplateResponse(
        "about.html",
        {"request": request, "locale": lang.code, "lang_prefix": lang.prefix},
    )


@web.get("/help", include_in_schema=False)
def web_help(request: Request, lang: LangPrefix = Depends(LangPrefix)) -> Any:
    return i18n_templates(lang.code).TemplateResponse(
        "help.html",
        {"request": request, "locale": lang.code, "lang_prefix": lang.prefix},
    )


@web.get("/search", include_in_schema=False)
def web_search(
    request: Request,
    response: Response,
    query: FulltextQuery = Depends(FulltextQuery),
    lang: LangPrefix = Depends(LangPrefix),
) -> Any:
    hits: Optional[FulltextHits] = None
    search_error: Optional[dict] = None
    status_code: int = 200
    if query.q is not None:
        try:
            hits = process_query(query)
        except ValueError as e:
            sentry_sdk.set_level("warning")
            sentry_sdk.capture_exception(e)
            search_error = {"type": "query", "message": str(e)}
            status_code = 400
        except IOError as e:
            sentry_sdk.capture_exception(e)
            search_error = {"type": "backend", "message": str(e)}
            status_code = 500

    headers = {}
    if hits and hits.query_wall_time_ms:
        headers[
            "Server-Timing"
        ] = f'es_wall;desc="Search API Request";dur={hits.query_wall_time_ms}'
        if hits.query_time_ms:
            headers[
                "Server-Timing"
            ] += f', es;desc="Search Internal Time";dur={hits.query_time_ms}'
    return i18n_templates(lang.code).TemplateResponse(
        "search.html",
        {
            "request": request,
            "locale": lang.code,
            "lang_prefix": lang.prefix,
            "hits": hits,
            "search_error": search_error,
            "query": query,
        },
        headers=headers,
        status_code=status_code,
    )


@web.get("/feed/rss", operation_id="get_feed_rss", include_in_schema=False)
def web_feed_rss(
    query: FulltextQuery = Depends(FulltextQuery),
    lang: LangPrefix = Depends(LangPrefix),
) -> fastapi_rss.RSSResponse:
    # override some query params for feeds
    original_query = query.q
    if query.q:
        query.q += " doc_type:work"
    query.offset = None
    query.filter_time = "past_year"
    query.sort_order = "time_desc"
    query.limit = 20

    hits: FulltextHits = process_query(query)

    rss_items = []
    for hit in hits.results:
        scholar_doc = hit["_obj"]
        abstract: Optional[str] = None
        if scholar_doc.abstracts:
            abstract = scholar_doc.abstracts[0].body
        authors = ", ".join(scholar_doc.biblio.contrib_names) or None
        pub_date = None
        if scholar_doc.biblio.release_date:
            # convert datetime.date to datetime.datetime
            pub_date = datetime.datetime(*scholar_doc.biblio.release_date.timetuple()[:6])
        rss_items.append(
            # NOTE(i18n): could prefer "original title" and abstract based on lang context
            fastapi_rss.Item(
                title=scholar_doc.biblio.title or "(Microfilm Page)",
                link=f"https://scholar.archive.org{lang.prefix}/work/{scholar_doc.work_ident}",
                description=abstract,
                author=authors,
                pub_date=pub_date,
                guid=fastapi_rss.GUID(content=scholar_doc.key),
            )
        )

    last_build_date = None
    if rss_items:
        last_build_date = rss_items[0].pub_date
    # i18n: unsure how to swap in translated strings here (in code, not in jinja2 template)
    feed = fastapi_rss.RSSFeed(
        title=f"IA Scholar Query: {original_query}",
        link=f"https://scholar.archive.org{lang.prefix}/",
        description="Internet Archive Scholar query results feed",
        language="en",
        last_build_date=last_build_date,
        docs=f"https://scholar.archive.org{lang.prefix}/help",
        generator="fatcat-scholar",
        webmaster="info@archive.org",
        ttl=60 * 24,  # 24 hours, in minutes
        item=rss_items,
    )
    return fastapi_rss.RSSResponse(feed)


@web.get("/work/{work_ident}", include_in_schema=False)
def web_work(
    request: Request,
    response: Response,
    work_ident: str = Path(..., min_length=20, max_length=30),
    lang: LangPrefix = Depends(LangPrefix),
) -> Any:
    doc = get_es_scholar_doc(f"work_{work_ident}")
    if not doc:
        raise HTTPException(status_code=404, detail="work not found")

    return i18n_templates(lang.code).TemplateResponse(
        "work.html",
        {
            "request": request,
            "locale": lang.code,
            "lang_prefix": lang.prefix,
            "doc": doc,
            "work": doc["_obj"],
        },
    )


def access_redirect_fallback(
    request: Request,
    work_ident: str,
    original_url: Optional[str] = None,
    archiveorg_path: Optional[str] = None,
) -> Any:
    """
    The purpose of this helper is to catch access redirects which would
    otherwise return a 404, and "try harder" to find a redirect.
    """
    # lookup against the live fatcat API, instead of scholar ES index
    api_conf = fcapi.Configuration()
    api_conf.host = settings.FATCAT_API_HOST
    api_client = fcapi.DefaultApi(fcapi.ApiClient(api_conf))

    # fetch list of releases for this work from current fatcat catalog. note
    # that these releases are not expanded (don't include file entities)
    try:
        # fetch work entity itself to fail fast (true 404) and handle redirects
        work_entity = api_client.get_work(work_ident)
        logger.warning(
            f"access_redirect_fallback: work_{work_ident} state={work_entity.state} redirect={work_entity.redirect}"
        )
        if work_entity.redirect:
            work_ident = work_entity.redirect
        partial_releases = api_client.get_work_releases(
            ident=work_ident,
            hide="abstracts,references",
        )
    except fcapi.ApiException as ae:
        raise HTTPException(
            status_code=ae.status,
            detail=f"Fatcat API call failed for work_{work_ident}",
        )

    # for each release, check for any archive.org access option with the given context
    for partial in partial_releases:
        release = api_client.get_release(
            partial.ident,
            expand="files",
            # TODO: expand="files,filesets,webcaptures",
            hide="abstracts,references",
        )
        if not release.files:
            continue
        for fe in release.files:
            for url_pair in fe.urls:
                access_url = url_pair.url
                if (
                    original_url
                    and "://web.archive.org/web/" in access_url
                    and access_url.endswith(original_url)
                ):
                    # TODO: test/verify this
                    timestamp = access_url.split("/")[4]
                    # if not (len(timestamp) == 14 and timestamp.isdigit()):
                    #    continue
                    # TODO: only add 'id_' for PDF replay
                    replay_url = f"https://web.archive.org/web/{timestamp}id_/{original_url}"
                    return RedirectResponse(replay_url, status_code=302)
                elif (
                    archiveorg_path
                    and "://archive.org/" in access_url
                    and archiveorg_path in access_url
                ):
                    return RedirectResponse(access_url, status_code=302)

    # give up and show an error page
    lang = LangPrefix(request)
    return i18n_templates(lang.code).TemplateResponse(
        "access_404.html",
        {
            "request": request,
            "locale": lang.code,
            "lang_prefix": lang.prefix,
            "work_ident": work_ident,
            "original_url": original_url,
            "archiveorg_path": archiveorg_path,
        },
        status_code=404,
    )


@web.get(
    "/work/{work_ident}/access/wayback/{url:path}",
    operation_id="access_redirect_wayback",
    include_in_schema=False,
)
def access_redirect_wayback(
    url: str,
    request: Request,
    work_ident: str = Path(..., min_length=20, max_length=30),
) -> Any:
    raw_original_url = "/".join(str(request.url).split("/")[7:])
    # the quote() call is necessary because the URL is un-encoded in the path parameter
    # see also: https://github.com/encode/starlette/commit/f997938916d20e955478f60406ef9d293236a16d
    original_url = urllib.parse.quote(
        raw_original_url,
        safe=":/%#?=@[]!$&'()*+,;",
    )
    doc_dict = get_es_scholar_doc(f"work_{work_ident}")
    if not doc_dict:
        return access_redirect_fallback(request, work_ident=work_ident, original_url=original_url)
    doc: ScholarDoc = doc_dict["_obj"]
    # combine fulltext with all access options
    access: List[Any] = []
    if doc.fulltext:
        access.append(doc.fulltext)
    access.extend(doc.access or [])
    for opt in access:
        if (
            opt.access_type == "wayback"
            and opt.access_url
            and "://web.archive.org/web/" in opt.access_url
            and opt.access_url.endswith(original_url)
        ):
            timestamp = opt.access_url.split("/")[4]
            if not (len(timestamp) == 14 and timestamp.isdigit()):
                continue
            # TODO: only add id_ for PDF replay
            access_url = f"https://web.archive.org/web/{timestamp}id_/{original_url}"
            return RedirectResponse(access_url, status_code=302)
    return access_redirect_fallback(request, work_ident=work_ident, original_url=original_url)


@web.get(
    "/work/{work_ident}/access/ia_file/{item}/{file_path:path}",
    operation_id="access_redirect_ia_file",
    include_in_schema=False,
)
def access_redirect_ia_file(
    item: str,
    file_path: str,
    request: Request,
    work_ident: str = Path(..., min_length=20, max_length=30),
) -> Any:
    original_path = urllib.parse.quote("/".join(str(request.url).split("/")[8:]))
    access_url = f"https://archive.org/download/{item}/{original_path}"
    doc_dict = get_es_scholar_doc(f"work_{work_ident}")
    if not doc_dict:
        return access_redirect_fallback(
            request, work_ident=work_ident, archiveorg_path=f"/{item}/{original_path}"
        )
    doc: ScholarDoc = doc_dict["_obj"]
    # combine fulltext with all access options
    access: List[Any] = []
    if doc.fulltext:
        access.append(doc.fulltext)
    access.extend(doc.access or [])
    for opt in access:
        if opt.access_type == "ia_file" and opt.access_url == access_url:
            return RedirectResponse(access_url, status_code=302)
    return access_redirect_fallback(
        request, work_ident=work_ident, archiveorg_path=f"/{item}/{original_path}"
    )


app = FastAPI(
    title="Internet Archive Scholar + Fatcat",
    description="IA Scholar is a project for preserving, indexing, and serving open access scholarly content. Fatcat is a public, bibliographic database of scholarly material. The Fatcat database can be consumed programmatically by a basic, public, read-only API.",
    version="0.2.6",
    #openapi_url="/api/openapi.json",
    #redoc_url="/api/redoc",
    #docs_url="/api/docs",
)

app.include_router(web)
for lang_option in I18N_LANG_OPTIONS:
    app.include_router(web, prefix=f"/{lang_option}")

app.include_router(fc_web_routes, prefix="/fatcat")
app.include_router(fc_api_routes, prefix="/api/fatcat")

app.mount("/static", StaticFiles(directory="src/scholar/static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Any:
    return FileResponse("src/scholar/static/ia-favicon.ico", media_type="image/x-icon")


@app.get("/sitemap.xml", include_in_schema=False)
async def basic_sitemap() -> Any:
    return FileResponse("src/scholar/static/sitemap.xml", media_type="application/xml")


ROBOTS_ALLOW = open("src/scholar/static/robots.allow.txt", "r").read()
ROBOTS_DISALLOW = open("src/scholar/static/robots.disallow.txt", "r").read()


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt(response_class: Any = PlainTextResponse) -> Any:
    if settings.SCHOLAR_ENV == "prod":
        return PlainTextResponse(ROBOTS_ALLOW)
    else:
        return PlainTextResponse(ROBOTS_DISALLOW)

@app.exception_handler(fcapi.ApiException)
async def unicorn_exception_handler(request: Request, ae: fcapi.ApiException) -> dict[str, Any]|Response:
    mimetype = "text/html"
    try:
        accept_header = request.headers.get("accept", "")
        if accept_header.startswith("application/json"):
            mimetype = "application/json"
    except Exception as e:
        logger.warning(f"exception handler failed: {e}")
        sentry_sdk.set_level("warning")
        sentry_sdk.capture_exception(e)

    try:
        json_body = json.loads(ae.body)
        if mimetype == "application/json":
            return json_body
        ae.error_name = json_body.get("error")
        ae.message = json_body.get("message")
    except ValueError:
        pass
    except TypeError:
        pass

    # TODO if the json does not serialize we'll return html even for "application/json"

    return fc_tmpls.TemplateResponse("api_error.html", {
        "request": request,
        "api_error": ae,
        }, status_code=ae.status)

@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException) -> templating._TemplateResponse|JSONResponse:
    """
    This is the generic handler for things like 404 errors.
    """
    mimetype = "text/html"
    try:
        accept_header = request.headers.get("accept", "")
        if accept_header.startswith("application/json"):
            mimetype = "application/json"
    except Exception as e:
        logger.warning(f"exception handler failed: {e}")
        sentry_sdk.set_level("warning")
        sentry_sdk.capture_exception(e)

    if mimetype == "text/html":
        lang = LangPrefix(request)
        return i18n_templates(lang.code).TemplateResponse(
            "error.html",
            {
                "request": request,
                "locale": lang.code,
                "lang_prefix": lang.prefix,
                "error": exc,
            },
            status_code=exc.status_code,
        )
    else:
        resp: Dict[str, Any] = {"status_code": exc.status_code}
        if exc.detail:
            resp["detail"] = exc.detail
        return JSONResponse(
            status_code=exc.status_code,
            content=resp,
        )


# configure middleware

#app.add_middleware(
#    CORSMiddleware,
#    allow_origins=["*"],
#    allow_credentials=False,
#    allow_methods=["GET"],
#    allow_headers=[],  # some defaults always enabled
#)

if settings.SENTRY_DSN:
    logger.info("Sentry integration enabled")
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SCHOLAR_ENV,
        max_breadcrumbs=10,
        release=GIT_REVISION,
    )
    app.add_middleware(SentryAsgiMiddleware)

if settings.ENABLE_PROMETHEUS:
    app.add_middleware(PrometheusMiddleware)
    app.add_route("/prometheus/", metrics)
