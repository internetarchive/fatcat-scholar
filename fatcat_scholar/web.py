"""
This contains the FastAPI web application and RESTful API.

So far there are few endpoints, so we just put them all here!
"""

import babel.support
from fastapi import FastAPI, APIRouter, Request, Depends, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse
from dynaconf import settings
from typing import Optional, Any

from fatcat_scholar.hacks import Jinja2Templates
from fatcat_scholar.search import do_fulltext_search, FulltextQuery, FulltextHits

# print(f"dynaconf settings: {settings.as_dict()}", file=sys.stderr)

I18N_LANG_TRANSLATIONS = ["de", "zh"]
I18N_LANG_OPTIONS = I18N_LANG_TRANSLATIONS + [
    settings.I18N_LANG_DEFAULT,
]


class LangPrefix:
    """
    Looks for a two-character language prefix.

    If there is no such prefix, in the future it could also look at the
    Accept-Language header and try to infer a language from that, while not
    setting the prefix code.
    """

    def __init__(self, request: Request):
        self.prefix: str = ""
        self.code: str = settings.I18N_LANG_DEFAULT
        for lang_option in I18N_LANG_OPTIONS:
            if request.url.path.startswith(f"/{lang_option}/"):
                self.prefix = f"/{lang_option}"
                self.code = lang_option
                break


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


@api.get("/search", operation_id="get_search")
async def search(query: FulltextQuery = Depends(FulltextQuery)) -> Any:
    return {"message": "search results would go here, I guess"}


web = APIRouter()


def locale_gettext(translations: Any) -> Any:
    def gt(s):  # noqa: ANN001,ANN201
        return translations.ugettext(s)

    return gt


def locale_ngettext(translations: Any) -> Any:
    def ngt(s, n):  # noqa: ANN001,ANN201
        return translations.ungettext(s)

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
            dirname="fatcat_scholar/translations", locales=[lang_opt],
        )
        templates = Jinja2Templates(
            directory="fatcat_scholar/templates", extensions=["jinja2.ext.i18n"],
        )
        templates.env.install_gettext_translations(translations, newstyle=True)
        templates.env.install_gettext_callables(
            locale_gettext(translations), locale_ngettext(translations), newstyle=True,
        )
        # remove a lot of whitespace in HTML output with these configs
        templates.env.trim_blocks = True
        templates.env.lstrip_blocks = True
        # pass-through application settings to be available in templates
        templates.env.globals["settings"] = settings
        d[lang_opt] = templates
    return d


i18n_templates = load_i18n_templates()


@web.get("/", include_in_schema=False)
async def web_home(
    request: Request,
    lang: LangPrefix = Depends(LangPrefix),
    content: ContentNegotiation = Depends(ContentNegotiation),
) -> Any:
    if content.mimetype == "application/json":
        return await home()
    return i18n_templates[lang.code].TemplateResponse(
        "home.html",
        {"request": request, "locale": lang.code, "lang_prefix": lang.prefix},
    )


@web.get("/about", include_in_schema=False)
async def web_about(request: Request, lang: LangPrefix = Depends(LangPrefix)) -> Any:
    return i18n_templates[lang.code].TemplateResponse(
        "about.html",
        {"request": request, "locale": lang.code, "lang_prefix": lang.prefix},
    )


@web.get("/help", include_in_schema=False)
async def web_help(request: Request, lang: LangPrefix = Depends(LangPrefix)) -> Any:
    return i18n_templates[lang.code].TemplateResponse(
        "help.html",
        {"request": request, "locale": lang.code, "lang_prefix": lang.prefix},
    )


@web.get("/search", include_in_schema=False)
async def web_search(
    request: Request,
    response: Response,
    query: FulltextQuery = Depends(FulltextQuery),
    lang: LangPrefix = Depends(LangPrefix),
    content: ContentNegotiation = Depends(ContentNegotiation),
) -> Any:

    if content.mimetype == "application/json":
        return await search(query)
    hits: Optional[FulltextHits] = None
    search_error: Optional[dict] = None
    status_code: int = 200
    if query.q is not None:
        try:
            hits = do_fulltext_search(query)
        except ValueError as e:
            search_error = dict(type="query", message=str(e))
            status_code = 400
        except IOError as e:
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
    return i18n_templates[lang.code].TemplateResponse(
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


app = FastAPI(
    title="Fatcat Scholar",
    description="Fulltext search interface for scholarly web content in the Fatcat catalog. An Internet Archive project.",
    version="0.1.0-dev",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc",
    docs_url="/api/docs",
)

app.include_router(web)
for lang_option in I18N_LANG_OPTIONS:
    app.include_router(web, prefix=f"/{lang_option}")

# Becasue we are mounting 'api' after 'web', the web routes will take
# precedence. Requests get passed through the API handlers based on content
# negotiation. This is counter-intuitive here in the code, but does seem to
# work, and results in the OpenAPI docs looking correct.
app.include_router(api)

app.mount("/static", StaticFiles(directory="fatcat_scholar/static"), name="static")

ROBOTS_ALLOW = open("fatcat_scholar/static/robots.allow.txt", "r").read()
ROBOTS_DISALLOW = open("fatcat_scholar/static/robots.disallow.txt", "r").read()


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt(response_class=PlainTextResponse) -> Any:
    print(ROBOTS_ALLOW)
    if settings.SCHOLAR_ENV == "prod":
        return PlainTextResponse(ROBOTS_ALLOW)
    else:
        return PlainTextResponse(ROBOTS_DISALLOW)
