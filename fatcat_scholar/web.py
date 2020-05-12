
"""
This file is the FastAPI web application.
"""

from enum import Enum

from fastapi import FastAPI, APIRouter, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

I18N_LANG_DEFAULT = "en"
I18N_LANG_OPTIONS = ["en", "de", "zh"]

class LangPrefix:
    """
    Looks for a two-character language prefix.

    If there is no such prefix, in the future it could also look at the
    Accept-Language header and try to infer a language from that, while not
    setting the prefix code.
    """

    def __init__(self, request: Request):
        self.prefix : str = ""
        self.code : str = I18N_LANG_DEFAULT
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
async def home(request: Request):
    return {"endpoints": {"/": "this", "/search": "fulltext search"}}

@api.get("/search", operation_id="get_search")
async def search(request: Request):
    return {"message": "search results would go here, I guess"}

web = APIRouter()
templates = Jinja2Templates(directory="fatcat_scholar/templates")

@web.get("/", include_in_schema=False)
async def web_home(request: Request, lang: LangPrefix = Depends(LangPrefix), content: ContentNegotiation = Depends(ContentNegotiation)):
    if content.mimetype == "application/json":
        return await api_home(request)
    return templates.TemplateResponse("home.html", {"request": request})

@web.get("/search", include_in_schema=False)
async def web_search(request: Request):
    if content.mimetype == "application/json":
        return await api_search(request)
    return templates.TemplateResponse("search.html", {"request": request})

app = FastAPI()


app.include_router(web)
for lang_option in I18N_LANG_OPTIONS:
    app.include_router(web, prefix=f"/{lang_option}")
app.include_router(api)
app.mount("/static", StaticFiles(directory="fatcat_scholar/static"), name="static")

