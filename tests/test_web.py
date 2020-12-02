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


def test_basic_api(client: Any) -> None:
    """
    Simple check of GET routes with application/json support
    """
    headers = {"Accept": "application/json"}
    resp = client.get("/", headers=headers)
    assert resp.status_code == 200
    assert resp.json()

    resp = client.get("/search", headers=headers)
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
