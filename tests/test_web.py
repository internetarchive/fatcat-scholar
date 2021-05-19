import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from fatcat_scholar.web import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_main_view(client: Any) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Internet Archive Scholar" in resp.content

    resp = client.get("/ar/")
    assert resp.status_code == 200
    assert "معلومات عن" in resp.content.decode("utf-8")

    resp = client.get("/", headers={"Accept-Language": "ar"})
    assert resp.status_code == 200
    assert "معلومات عن" in resp.content.decode("utf-8")

    resp = client.get("/", headers={"Accept-Language": "zh_Hans_CN"})
    assert resp.status_code == 200
    assert "我们是" in resp.content.decode("utf-8")


def test_basic_api(client: Any, mocker: Any) -> None:
    """
    Simple check of GET routes with application/json support
    """
    headers = {"Accept": "application/json"}
    resp = client.get("/", headers=headers)
    assert resp.status_code == 200
    assert resp.json()

    # request with no 'q' parameter is an error
    resp = client.get("/search", headers=headers)
    assert resp.status_code == 400

    with open("tests/files/elastic_fulltext_search.json") as f:
        elastic_resp = json.loads(f.read())

    es_raw = mocker.patch(
        "elasticsearch.connection.Urllib3HttpConnection.perform_request"
    )
    es_raw.side_effect = [
        (200, {}, json.dumps(elastic_resp)),
    ]

    resp = client.get("/search?q=blood", headers=headers)
    assert resp.status_code == 200
    assert resp.json()


def test_basic_routes(client: Any) -> None:
    """
    Simple check of GET routes in the web app
    """

    resp = client.get("/robots.txt")
    assert resp.status_code == 200

    resp = client.get("/static/ia-logo.svg")
    assert resp.status_code == 200

    LANG_PREFIX_LIST = ["", "/ar"]
    PATH_LIST = ["/", "/about", "/help", "/search"]

    for lang in LANG_PREFIX_LIST:
        for path in PATH_LIST:
            resp = client.get(lang + path)
            assert resp.status_code == 200
            assert b"</body>" in resp.content


def test_basic_search(client: Any, mocker: Any) -> None:

    rv = client.get("/search")
    assert rv.status_code == 200

    with open("tests/files/elastic_fulltext_search.json") as f:
        elastic_resp = json.loads(f.read())

    es_raw = mocker.patch(
        "elasticsearch.connection.Urllib3HttpConnection.perform_request"
    )
    es_raw.side_effect = [
        (200, {}, json.dumps(elastic_resp)),
        (200, {}, json.dumps(elastic_resp)),
    ]

    rv = client.get("/search?q=blood")
    assert rv.status_code == 200
    assert b"Hits" in rv.content

    rv = client.get("/zh/search?q=blood")
    assert rv.status_code == 200


def test_basic_work_landing_page(client: Any, mocker: Any) -> None:

    with open("tests/files/elastic_fulltext_get.json") as f:
        elastic_resp = json.loads(f.read())

    es_raw = mocker.patch(
        "elasticsearch.connection.Urllib3HttpConnection.perform_request"
    )
    es_raw.side_effect = [
        (200, {}, json.dumps(elastic_resp)),
        (200, {}, json.dumps(elastic_resp)),
    ]

    rv = client.get("/work/2x5qvct2dnhrbctqa2q2uyut6a")
    assert rv.status_code == 200
    assert b"citation_pdf_url" in rv.content

    rv = client.get("/zh/work/2x5qvct2dnhrbctqa2q2uyut6a")
    assert rv.status_code == 200


def test_basic_access_redirect(client: Any, mocker: Any) -> None:
    """
    NOTE: DEPRECATED
    """

    with open("tests/files/elastic_fulltext_search.json") as f:
        elastic_resp = json.loads(f.read())

    es_raw = mocker.patch(
        "elasticsearch.connection.Urllib3HttpConnection.perform_request"
    )
    es_raw.side_effect = [
        (200, {}, json.dumps(elastic_resp)),
        (200, {}, json.dumps(elastic_resp)),
    ]

    rv = client.get(
        "/access-redirect/f81f84e23c9ba5d364c70f01fa26e645d29c0427.pdf",
        allow_redirects=False,
    )
    assert rv.status_code == 302
    assert (
        rv.headers["Location"]
        == "https://web.archive.org/web/20200206164725id_/https://www.federalreserve.gov/econresdata/feds/2015/files/2015118pap.pdf"
    )

    rv = client.get(
        "/access-redirect/aaaaaaaaaaaaaaaaaaaaaa01fa26e645d29c0427.pdf",
        allow_redirects=False,
    )
    assert rv.status_code == 404


def test_access_redirects(client: Any, mocker: Any) -> None:

    # tricky "URL encoding in archive.org path" case
    rv = client.get(
        "/access/ia_file/crossref-pre-1909-scholarly-works/10.1016%252Fs0140-6736%252802%252912493-7.zip/10.1016%252Fs0140-6736%252802%252912928-x.pdf",
        allow_redirects=False,
    )
    assert rv.status_code == 302
    assert (
        rv.headers["Location"]
        == "https://archive.org/download/crossref-pre-1909-scholarly-works/10.1016%252Fs0140-6736%252802%252912493-7.zip/10.1016%252Fs0140-6736%252802%252912928-x.pdf"
    )

    rv = client.get(
        "/access/wayback/20170814015956/https://epub.uni-regensburg.de/21901/1/lorenz73.pdf",
        allow_redirects=False,
    )
    assert rv.status_code == 302
    assert (
        rv.headers["Location"]
        == "https://web.archive.org/web/20170814015956id_/https://epub.uni-regensburg.de/21901/1/lorenz73.pdf"
    )

    # spaces ("%20" vs "+")
    rv = client.get(
        "/access/wayback/20170811115414/http://sudjms.net/issues/5-4/pdf/8)A%20comparison%20study%20of%20histochemical%20staining%20of%20various%20tissues%20after.pdf",
        allow_redirects=False,
    )
    assert rv.status_code == 302
    assert (
        rv.headers["Location"]
        == "https://web.archive.org/web/20170811115414id_/http://sudjms.net/issues/5-4/pdf/8)A%20comparison%20study%20of%20histochemical%20staining%20of%20various%20tissues%20after.pdf"
    )
