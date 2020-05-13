"""
This contains the FastAPI web application and RESTful API.

So far there are few endpoints, so we just put them all here!
"""

from enum import Enum

import babel.support
from fastapi import FastAPI, APIRouter, Request, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dynaconf import settings

from fatcat_scholar.hacks import Jinja2Templates
from fatcat_scholar.search import do_fulltext_search

print(settings.as_dict())

I18N_LANG_TRANSLATIONS = ["de", "zh"]
I18N_LANG_OPTIONS = I18N_LANG_TRANSLATIONS + [settings.I18N_LANG_DEFAULT,]

class SearchParams(BaseModel):
    q: str = ""

class LangPrefix:
    """
    Looks for a two-character language prefix.

    If there is no such prefix, in the future it could also look at the
    Accept-Language header and try to infer a language from that, while not
    setting the prefix code.
    """

    def __init__(self, request: Request):
        self.prefix : str = ""
        self.code : str = settings.I18N_LANG_DEFAULT
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
        if request.headers.get('accept', '').startswith('application/json'):
            self.mimetype = "application/json"

api = APIRouter()

@api.get("/", operation_id="get_home")
async def home():
    return {"endpoints": {"/": "this", "/search": "fulltext search"}}

@api.get("/search", operation_id="get_search")
async def search(query: SearchParams = Depends(SearchParams)):
    return {"message": "search results would go here, I guess"}

web = APIRouter()

def locale_gettext(translations):
    def gt(s):
        return translations.ugettext(s)
    return gt

def locale_ngettext(translations):
    def ngt(s, n):
        return translations.ungettext(s)
    return ngt

def load_i18n_templates():
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
            extensions=["jinja2.ext.i18n"],
        )
        templates.env.install_gettext_translations(translations, newstyle=True)
        templates.env.install_gettext_callables(
            locale_gettext(translations),
            locale_ngettext(translations),
            newstyle=True,
        )
        templates.env.globals['settings'] = settings
        d[lang_opt] = templates
    return d

i18n_templates = load_i18n_templates()

@web.get("/", include_in_schema=False)
async def web_home(request: Request, lang: LangPrefix = Depends(LangPrefix), content: ContentNegotiation = Depends(ContentNegotiation)):
    if content.mimetype == "application/json":
        return await home()
    return i18n_templates[lang.code].TemplateResponse("home.html", {"request": request, "locale": lang.code, "lang_prefix": lang.prefix})

@web.get("/about", include_in_schema=False)
async def web_about(request: Request, lang: LangPrefix = Depends(LangPrefix)):
    return i18n_templates[lang.code].TemplateResponse("about.html", {"request": request, "locale": lang.code, "lang_prefix": lang.prefix})

@web.get("/search", include_in_schema=False)
async def web_search(request: Request, query: SearchParams = Depends(SearchParams), lang: LangPrefix = Depends(LangPrefix), content: ContentNegotiation = Depends(ContentNegotiation)):
    if content.mimetype == "application/json":
        return await search(query)
    found = None
    if query.q:
        found = do_fulltext_search(query.q)
    return i18n_templates[lang.code].TemplateResponse("search.html", {"request": request, "locale": lang.code, "lang_prefix": lang.prefix, "found": found})


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

