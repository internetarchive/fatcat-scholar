"""
This contains the FastAPI web application and RESTful API.

So far there are few endpoints, so we just put them all here!
"""

import datetime
import logging
import urllib.parse
from typing import Any, Dict, List, Optional

import babel.numbers
import babel.support
import fastapi_rss
import fatcat_openapi_client
import sentry_sdk
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette_prometheus import PrometheusMiddleware, metrics

from fatcat_scholar.config import GIT_REVISION, settings
from fatcat_scholar.hacks import (
    Jinja2Templates,
    make_access_redirect_url,
    parse_accept_lang,
)
from fatcat_scholar.schema import ScholarDoc
from fatcat_scholar.search import (
    FulltextHits,
    FulltextQuery,
    es_scholar_index_alive,
    get_es_scholar_doc,
    process_query,
)

logger = logging.getLogger()

I18N_LANG_TRANSLATIONS = [
    "ar",
    "de",
    "el",
    "es",
    "fa",
    "fr",
    "hr",
    "it",
    "ko",
    "nb",
    "nl",
    "pt",
    "ru",
    "zh",
]
I18N_LANG_OPTIONS = I18N_LANG_TRANSLATIONS + [
    settings.I18N_LANG_DEFAULT,
]


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


class ContentNegotiation:
    """
    Choses a mimetype to return based on Accept header.

    Intended to be used for RESTful content negotiation from web endpoints to API.
    """

    def __init__(self, request: Request):
        self.mimetype = "text/html"
        if request.headers.get("accept", "").startswith("application/json"):
            self.mimetype = "application/json"


api = APIRouter()


@api.get("/", operation_id="get_home")
async def home() -> Any:
    return {"endpoints": {"/": "this", "/search": "fulltext search"}}


@api.head("/", include_in_schema=False)
async def root_head() -> Any:
    """
    HTTP HEAD only for the root path (and health check below). Requested by,
    eg, uptime monitoring tools. This is distinct from the CORS middleware (for
    OPTION).
    """
    return Response()


@api.get("/_health", operation_id="get_health")
def health_get() -> Any:
    """
    Checks that connection back to elasticsearch index is working.
    """
    if not es_scholar_index_alive():
        raise HTTPException(status_code=503)
    return Response()


@api.head("/_health", include_in_schema=False)
def health_head() -> Any:
    return health_get()


class HitsModel(BaseModel):
    count_returned: int
    count_found: int
    offset: int
    limit: int
    query_time_ms: int
    query_wall_time_ms: int
    results: List[ScholarDoc]


@api.get("/search", operation_id="get_search", response_model=HitsModel)
def search(query: FulltextQuery = Depends(FulltextQuery)) -> FulltextHits:
    hits: Optional[FulltextHits] = None
    if query.q is None:
        raise HTTPException(status_code=400, detail="Expected a 'q' query parameter")
    try:
        hits = process_query(query)
    except ValueError as e:
        sentry_sdk.set_level("warning")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=400, detail=f"Query Error: {e}")
    except IOError as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Backend Error: {e}")

    # remove internal context from hit objects
    for doc in hits.results:
        doc.pop("_obj", None)

    return hits


@api.get("/work/{work_ident}", operation_id="get_work")
def get_work(work_ident: str = Query(..., min_length=20, max_length=20)) -> dict:
    doc = get_es_scholar_doc(f"work_{work_ident}")
    if not doc:
        raise HTTPException(status_code=404, detail="work not found")
    doc.pop("_obj", None)
    return doc


web = APIRouter()


def locale_gettext(translations: Any) -> Any:
    def gt(s):  # noqa: ANN001,ANN201
        return translations.ugettext(s)

    return gt


def locale_ngettext(translations: Any) -> Any:
    def ngt(s, p, n):  # noqa: ANN001,ANN201
        return translations.ungettext(s, p, n)

    return ngt


def load_i18n_templates() -> Any:
    """
    This is a hack to work around lack of per-request translation
    (babel/gettext) locale switching in FastAPI and Starlette. Flask (and
    presumably others) get around this using global context (eg, in
    Flask-Babel).

    See related issues:

    - https://github.com/encode/starlette/issues/279
    - https://github.com/aio-libs/aiohttp-jinja2/issues/187
    """

    d = dict()
    for lang_opt in I18N_LANG_OPTIONS:
        translations = babel.support.Translations.load(
            dirname="fatcat_scholar/translations",
            locales=[lang_opt],
        )
        templates = Jinja2Templates(
            directory="fatcat_scholar/templates",
            extensions=["jinja2.ext.i18n", "jinja2.ext.do"],
        )
        templates.env.install_gettext_translations(translations, newstyle=True)  # type: ignore
        templates.env.install_gettext_callables(  # type: ignore
            locale_gettext(translations),
            locale_ngettext(translations),
            newstyle=True,
        )
        # remove a lot of whitespace in HTML output with these configs
        templates.env.trim_blocks = True
        templates.env.lstrip_blocks = True
        # pass-through application settings to be available in templates
        templates.env.globals["settings"] = settings
        templates.env.globals["babel_numbers"] = babel.numbers
        templates.env.globals["make_access_redirect_url"] = make_access_redirect_url
        d[lang_opt] = templates
    return d


I18N_TEMPLATES = load_i18n_templates()


@web.get("/", include_in_schema=False)
async def web_home(
    request: Request,
    lang: LangPrefix = Depends(LangPrefix),
    content: ContentNegotiation = Depends(ContentNegotiation),
) -> Any:
    if content.mimetype == "application/json":
        return await home()
    return I18N_TEMPLATES[lang.code].TemplateResponse(
        "home.html",
        {"request": request, "locale": lang.code, "lang_prefix": lang.prefix},
    )


@web.get("/about", include_in_schema=False)
async def web_about(request: Request, lang: LangPrefix = Depends(LangPrefix)) -> Any:
    return I18N_TEMPLATES[lang.code].TemplateResponse(
        "about.html",
        {"request": request, "locale": lang.code, "lang_prefix": lang.prefix},
    )


@web.get("/help", include_in_schema=False)
async def web_help(request: Request, lang: LangPrefix = Depends(LangPrefix)) -> Any:
    return I18N_TEMPLATES[lang.code].TemplateResponse(
        "help.html",
        {"request": request, "locale": lang.code, "lang_prefix": lang.prefix},
    )


@web.get("/search", include_in_schema=False)
def web_search(
    request: Request,
    response: Response,
    query: FulltextQuery = Depends(FulltextQuery),
    lang: LangPrefix = Depends(LangPrefix),
    content: ContentNegotiation = Depends(ContentNegotiation),
) -> Any:

    if content.mimetype == "application/json":
        return search(query)
    hits: Optional[FulltextHits] = None
    search_error: Optional[dict] = None
    status_code: int = 200
    if query.q is not None:
        try:
            hits = process_query(query)
        except ValueError as e:
            sentry_sdk.set_level("warning")
            sentry_sdk.capture_exception(e)
            search_error = dict(type="query", message=str(e))
            status_code = 400
        except IOError as e:
            sentry_sdk.capture_exception(e)
            search_error = dict(type="backend", message=str(e))
            status_code = 500

    headers = dict()
    if hits and hits.query_wall_time_ms:
        headers[
            "Server-Timing"
        ] = f'es_wall;desc="Search API Request";dur={hits.query_wall_time_ms}'
        if hits.query_time_ms:
            headers[
                "Server-Timing"
            ] += f', es;desc="Search Internal Time";dur={hits.query_time_ms}'
    return I18N_TEMPLATES[lang.code].TemplateResponse(
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
            pub_date = datetime.datetime(
                *scholar_doc.biblio.release_date.timetuple()[:6]
            )
        rss_items.append(
            # NOTE(i18n): could prefer "original title" and abstract based on lang context
            fastapi_rss.Item(
                title=scholar_doc.biblio.title or f"(Microfilm Page)",
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
    work_ident: str = Query(..., min_length=20, max_length=20),
    lang: LangPrefix = Depends(LangPrefix),
    content: ContentNegotiation = Depends(ContentNegotiation),
) -> Any:

    if content.mimetype == "application/json":
        return get_work(work_ident)

    doc = get_es_scholar_doc(f"work_{work_ident}")
    if not doc:
        raise HTTPException(status_code=404, detail="work not found")

    return I18N_TEMPLATES[lang.code].TemplateResponse(
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
    api_conf = fatcat_openapi_client.Configuration()
    api_conf.host = settings.FATCAT_API_HOST
    api_client = fatcat_openapi_client.DefaultApi(
        fatcat_openapi_client.ApiClient(api_conf)
    )

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
    except fatcat_openapi_client.ApiException as ae:
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
                    replay_url = (
                        f"https://web.archive.org/web/{timestamp}id_/{original_url}"
                    )
                    return RedirectResponse(replay_url, status_code=302)
                elif (
                    archiveorg_path
                    and "://archive.org/" in access_url
                    and archiveorg_path in access_url
                ):
                    return RedirectResponse(access_url, status_code=302)

    # give up and show an error page
    lang = LangPrefix(request)
    return I18N_TEMPLATES[lang.code].TemplateResponse(
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
    work_ident: str = Query(..., min_length=20, max_length=20),
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
        return access_redirect_fallback(
            request, work_ident=work_ident, original_url=original_url
        )
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
    return access_redirect_fallback(
        request, work_ident=work_ident, original_url=original_url
    )


@web.get(
    "/work/{work_ident}/access/ia_file/{item}/{file_path:path}",
    operation_id="access_redirect_ia_file",
    include_in_schema=False,
)
def access_redirect_ia_file(
    item: str,
    file_path: str,
    request: Request,
    work_ident: str = Query(..., min_length=20, max_length=20),
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
    title="Fatcat Scholar",
    description="Fulltext search interface for scholarly web content in the Fatcat catalog. An Internet Archive project.",
    version="0.2.0-dev",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc",
    docs_url="/api/docs",
)

app.include_router(web)
for lang_option in I18N_LANG_OPTIONS:
    app.include_router(web, prefix=f"/{lang_option}")

# Because we are mounting 'api' after 'web', the web routes will take
# precedence. Requests get passed through the API handlers based on content
# negotiation. This is counter-intuitive here in the code, but does seem to
# work, and results in the OpenAPI docs looking correct.
app.include_router(api)

app.mount("/static", StaticFiles(directory="fatcat_scholar/static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Any:
    return FileResponse(
        "fatcat_scholar/static/ia-favicon.ico", media_type="image/x-icon"
    )


@app.get("/sitemap.xml", include_in_schema=False)
async def basic_sitemap() -> Any:
    return FileResponse(
        "fatcat_scholar/static/sitemap.xml", media_type="application/xml"
    )


ROBOTS_ALLOW = open("fatcat_scholar/static/robots.allow.txt", "r").read()
ROBOTS_DISALLOW = open("fatcat_scholar/static/robots.disallow.txt", "r").read()


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt(response_class: Any = PlainTextResponse) -> Any:
    if settings.SCHOLAR_ENV == "prod":
        return PlainTextResponse(ROBOTS_ALLOW)
    else:
        return PlainTextResponse(ROBOTS_DISALLOW)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> Any:
    """
    This is the generic handler for things like 404 errors.
    """
    # TODO: what if there is an error in any of the detection code?
    content = ContentNegotiation(request)

    if content.mimetype == "text/html":
        lang = LangPrefix(request)
        return I18N_TEMPLATES[lang.code].TemplateResponse(
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=[],  # some defaults always enabled
)

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
