import typing
import jinja2

from starlette.background import BackgroundTask
from starlette.templating import _TemplateResponse


class Jinja2Templates:
    """
    This is a patched version of starlette.templating.Jinja2Templates that
    supports extensions (list of strings) passed to jinja2.Environment
    """

    def __init__(self, directory: str, extensions: typing.List[str] = []) -> None:
        assert jinja2 is not None, "jinja2 must be installed to use Jinja2Templates"
        self.env = self.get_env(directory, extensions)

    def get_env(
        self, directory: str, extensions: typing.List[str] = []
    ) -> "jinja2.Environment":
        @jinja2.contextfunction
        def url_for(context: dict, name: str, **path_params: typing.Any) -> str:
            request = context["request"]
            return request.url_for(name, **path_params)

        loader = jinja2.FileSystemLoader(directory)
        env = jinja2.Environment(loader=loader, extensions=extensions, autoescape=True)
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
    assert parse_accept_lang("", []) == None
    assert parse_accept_lang("en,de", []) == None
    assert parse_accept_lang("en,de", ["en"]) == "en"
    assert parse_accept_lang("en-GB,de", ["en"]) == "en"
    assert parse_accept_lang("zh_Hans_CN", ["en", "zh"]) == "zh"
    assert parse_accept_lang("en,de", ["de"]) == "de"
    assert (
        parse_accept_lang("en-ca,en;q=0.8,en-us;q=0.6,de-de;q=0.4,de;q=0.2", ["de"])
        == "de"
    )
    assert (
        parse_accept_lang(
            "en-ca,en;q=0.8,en-us;q=0.6,de-de;q=0.4,de;q=0.2", ["en", "de"]
        )
        == "en"
    )
    assert (
        parse_accept_lang("en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7", ["zh", "en", "de"])
        == "en"
    )


def wayback_direct_url(url: str) -> str:
    """
    Re-writes a wayback replay URL to add the 'id_' suffix (or equivalent for direct file access)
    """
    if not "://web.archive.org" in url:
        return url
    segments = url.split("/")
    if len(segments) < 6 or not segments[4].isdigit():
        return url
    segments[4] += "id_"
    return "/".join(segments)


def test_wayback_direct_url() -> None:
    assert (
        wayback_direct_url("http://fatcat.wiki/thing.pdf")
        == "http://fatcat.wiki/thing.pdf"
    )
    assert (
        wayback_direct_url("https://web.archive.org/web/*/http://fatcat.wiki/thing.pdf")
        == "https://web.archive.org/web/*/http://fatcat.wiki/thing.pdf"
    )
    assert (
        wayback_direct_url(
            "https://web.archive.org/web/1234/http://fatcat.wiki/thing.pdf"
        )
        == "https://web.archive.org/web/1234id_/http://fatcat.wiki/thing.pdf"
    )


def make_access_redirect_url(access_type: str, access_url: str) -> str:
    if access_type == "wayback" and "://web.archive.org/" in access_url:
        segments = access_url.split("/")
        dt = segments[4]
        original_url = "/".join(segments[5:])
        return f"https://scholar.archive.org/access/wayback/{dt}/{original_url}"
    elif access_type == "ia_file" and "://archive.org/download/" in access_url:
        suffix = "/".join(access_url.split("/")[4:])
        return f"https://scholar.archive.org/access/ia_file/{suffix}"
    else:
        return access_url


def test_make_access_redirect_url() -> None:
    assert (
        make_access_redirect_url(
            "wayback", "https://web.archive.org/web/1234/http://fatcat.wiki/thing.pdf"
        )
        == "https://scholar.archive.org/access/wayback/1234/http://fatcat.wiki/thing.pdf"
    )
    assert (
        make_access_redirect_url(
            "wayback",
            "https://web.archive.org/web/1234/http://fatcat.wiki/thing.pdf?param=asdf",
        )
        == "https://scholar.archive.org/access/wayback/1234/http://fatcat.wiki/thing.pdf?param=asdf"
    )
    assert (
        make_access_redirect_url(
            "ia_file", "https://archive.org/download/something/file.pdf"
        )
        == "https://scholar.archive.org/access/ia_file/something/file.pdf"
    )
    assert (
        make_access_redirect_url("blah", "https://mit.edu/file.pdf")
        == "https://mit.edu/file.pdf"
    )
