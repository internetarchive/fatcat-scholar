import typing

import babel.numbers
import babel.support
import jinja2
from starlette.background import BackgroundTask
from starlette.templating import _TemplateResponse

from scholar.config import I18N_LANG_OPTIONS, settings

TEMPLATE_LOADER = jinja2.FileSystemLoader("src/scholar/templates")


class Jinja2Templates:
    """
    This is a patched version of starlette.templating.Jinja2Templates that
    supports extensions (list of strings) passed to jinja2.Environment
    """

    def __init__(self, extensions: typing.List[str] = []) -> None:
        assert jinja2 is not None, "jinja2 must be installed to use Jinja2Templates"
        self.env = self.get_env(extensions)

    def get_env(self, extensions: typing.List[str] = []) -> "jinja2.Environment":
        @jinja2.pass_context
        def url_for(context: dict, name: str, **path_params: typing.Any) -> str:
            request = context["request"]
            return request.url_for(name, **path_params)

        env = jinja2.Environment(loader=TEMPLATE_LOADER, extensions=extensions, autoescape=True)
        env.globals["url_for"] = url_for
        return env

    def get_template(self, name: str) -> "jinja2.Template":
        return self.env.get_template(name)

    def TemplateResponse(
        self,
        name: str,
        context: dict,
        status_code: int = 200,
        headers: dict = None,
        media_type: str = None,
        background: BackgroundTask = None,
    ) -> _TemplateResponse:
        if "request" not in context:
            raise ValueError('context must include a "request" key')
        template = self.get_template(name)
        return _TemplateResponse(
            template,
            context,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )


def load_i18n_files() -> typing.Any:
    """
    This is a hack to work around lack of per-request translation
    (babel/gettext) locale switching in FastAPI and Starlette. Flask (and
    presumably others) get around this using global context (eg, in
    Flask-Babel).

    See related issues:

    - https://github.com/encode/starlette/issues/279
    - https://github.com/aio-libs/aiohttp-jinja2/issues/187
    """
    d = {}
    for lang_opt in I18N_LANG_OPTIONS:
        translations = babel.support.Translations.load(
            dirname="src/scholar/translations",
            locales=[lang_opt],
        )
        d[lang_opt] = translations
    return d


I18N_TRANSLATION_FILES = load_i18n_files()


def locale_gettext(translations: typing.Any) -> typing.Any:
    def gt(s):  # noqa: ANN001,ANN201,ANN202
        return translations.ugettext(s)

    return gt


def locale_ngettext(translations: typing.Any) -> typing.Any:
    def ngt(s, p, n):  # noqa: ANN001,ANN201,ANN202
        return translations.ungettext(s, p, n)

    return ngt


def i18n_templates(locale: str) -> Jinja2Templates:
    """
    This is a hack to work around lack of per-request translation
    (babel/gettext) locale switching in FastAPI and Starlette. Flask (and
    presumably others) get around this using global context (eg, in
    Flask-Babel).

    The intent is to call this function and create a new Jinja2 Environment for
    a specific language separately within a request (aka, not shared between
    requests), when needed. This is inefficient but should resolve issues with
    cross-request poisoning, both in threading (threadpool) or async
    concurrency.

    See related issues:

    - https://github.com/encode/starlette/issues/279
    - https://github.com/aio-libs/aiohttp-jinja2/issues/187
    """

    translations = I18N_TRANSLATION_FILES[locale]
    templates = Jinja2Templates(
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
    return templates


def parse_accept_lang(header: str, options: typing.List[str]) -> typing.Optional[str]:
    """
    Crude HTTP Accept-Language content negotiation.
    Assumes that languages are specified in order of priority, etc.
    """
    if not header:
        return None
    chunks = [v.split(";")[0].split("-")[0].split("_")[0] for v in header.split(",")]
    for c in chunks:
        if len(c) == 2 and c in options:
            return c
    return None


def test_parse_accept_lang() -> None:
    assert parse_accept_lang("", []) is None
    assert parse_accept_lang("en,de", []) is None
    assert parse_accept_lang("en,de", ["en"]) == "en"
    assert parse_accept_lang("en-GB,de", ["en"]) == "en"
    assert parse_accept_lang("zh_Hans_CN", ["en", "zh"]) == "zh"
    assert parse_accept_lang("en,de", ["de"]) == "de"
    assert parse_accept_lang("en-ca,en;q=0.8,en-us;q=0.6,de-de;q=0.4,de;q=0.2", ["de"]) == "de"
    assert (
        parse_accept_lang("en-ca,en;q=0.8,en-us;q=0.6,de-de;q=0.4,de;q=0.2", ["en", "de"]) == "en"
    )
    assert parse_accept_lang("en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7", ["zh", "en", "de"]) == "en"


def wayback_direct_url(url: str) -> str:
    """
    Re-writes a wayback replay URL to add the 'id_' suffix (or equivalent for direct file access)
    """
    if "://web.archive.org" not in url:
        return url
    segments = url.split("/")
    if len(segments) < 6 or not segments[4].isdigit():
        return url
    segments[4] += "id_"
    return "/".join(segments)


def test_wayback_direct_url() -> None:
    assert wayback_direct_url("http://scholar.archive.org/fatcat/thing.pdf") == "http://scholar.archive.org/fatcat/thing.pdf"
    assert (
        wayback_direct_url("https://web.archive.org/web/*/http://scholar.archive.org/fatcat/thing.pdf")
        == "https://web.archive.org/web/*/http://scholar.archive.org/fatcat/thing.pdf"
    )
    assert (
        wayback_direct_url("https://web.archive.org/web/1234/http://scholar.archive.org/fatcat/thing.pdf")
        == "https://web.archive.org/web/1234id_/http://scholar.archive.org/fatcat/thing.pdf"
    )
    assert (
        wayback_direct_url(
            "https://web.archive.org/web/20170811115414/http://sudjms.net/issues/5-4/pdf/8)A%20comparison%20study%20of%20histochemical%20staining%20of%20various%20tissues%20after.pdf"
        )
        == "https://web.archive.org/web/20170811115414id_/http://sudjms.net/issues/5-4/pdf/8)A%20comparison%20study%20of%20histochemical%20staining%20of%20various%20tissues%20after.pdf"
    )


def make_access_redirect_url(work_ident: str, access_type: str, access_url: str) -> str:
    if access_type == "wayback" and "://web.archive.org/" in access_url:
        segments = access_url.split("/")
        original_url = "/".join(segments[5:])
        return f"https://scholar.archive.org/work/{work_ident}/access/wayback/{original_url}"
    elif access_type == "ia_file" and "://archive.org/download/" in access_url:
        suffix = "/".join(access_url.split("/")[4:])
        return f"https://scholar.archive.org/work/{work_ident}/access/ia_file/{suffix}"
    else:
        return access_url


def test_make_access_redirect_url() -> None:
    assert (
        make_access_redirect_url(
            "lmobci36t5aelogzjsazuwxpie",
            "wayback",
            "https://web.archive.org/web/1234/http://scholar.archive.org/fatcat/thing.pdf",
        )
        == "https://scholar.archive.org/work/lmobci36t5aelogzjsazuwxpie/access/wayback/http://scholar.archive.org/fatcat/thing.pdf"
    )
    assert (
        make_access_redirect_url(
            "lmobci36t5aelogzjsazuwxpie",
            "wayback",
            "https://web.archive.org/web/1234/http://scholar.archive.org/fatcat/thing.pdf?param=asdf",
        )
        == "https://scholar.archive.org/work/lmobci36t5aelogzjsazuwxpie/access/wayback/http://scholar.archive.org/fatcat/thing.pdf?param=asdf"
    )
    assert (
        make_access_redirect_url(
            "lmobci36t5aelogzjsazuwxpie",
            "ia_file",
            "https://archive.org/download/something/file.pdf",
        )
        == "https://scholar.archive.org/work/lmobci36t5aelogzjsazuwxpie/access/ia_file/something/file.pdf"
    )
    assert (
        make_access_redirect_url("lmobci36t5aelogzjsazuwxpie", "blah", "https://mit.edu/file.pdf")
        == "https://mit.edu/file.pdf"
    )
    assert (
        make_access_redirect_url(
            "lmobci36t5aelogzjsazuwxpie",
            "wayback",
            "https://web.archive.org/web/20170811115414/http://sudjms.net/issues/5-4/pdf/8)A%20comparison%20study%20of%20histochemical%20staining%20of%20various%20tissues%20after.pdf",
        )
        == "https://scholar.archive.org/work/lmobci36t5aelogzjsazuwxpie/access/wayback/http://sudjms.net/issues/5-4/pdf/8)A%20comparison%20study%20of%20histochemical%20staining%20of%20various%20tissues%20after.pdf"
    )
