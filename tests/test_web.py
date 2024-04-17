import json
from typing import Any

import fatcat_openapi_client
import pytest
from fastapi.testclient import TestClient

from scholar.web import app


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


#def test_basic_api(client: Any, mocker: Any) -> None:
#    """
#    Simple check of GET routes with application/json support
#    """
#    headers = {"Accept": "application/json"}
#    resp = client.get("/", headers=headers)
#    assert resp.status_code == 200
#    assert resp.json()
#
#    # request with no 'q' parameter is an error
#    resp = client.get("/search", headers=headers)
#    assert resp.status_code == 400
#
#    with open("tests/files/elastic_fulltext_search.json") as f:
#        elastic_resp = json.loads(f.read())
#
#    es_raw = mocker.patch("elasticsearch.connection.Urllib3HttpConnection.perform_request")
#    es_raw.side_effect = [
#        (200, {}, json.dumps(elastic_resp)),
#    ]
#
#    resp = client.get("/search?q=blood", headers=headers)
#    assert resp.status_code == 200
#    assert resp.json()


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

    es_raw = mocker.patch("elasticsearch.connection.Urllib3HttpConnection.perform_request")
    es_raw.side_effect = [
        (200, {}, json.dumps(elastic_resp)),
        (200, {}, json.dumps(elastic_resp)),
    ]

    rv = client.get("/search?q=blood")
    assert rv.status_code == 200
    assert b"Hits" in rv.content

    rv = client.get("/zh/search?q=blood")
    assert rv.status_code == 200


def test_basic_rss_feed(client: Any, mocker: Any) -> None:
    with open("tests/files/elastic_fulltext_search.json") as f:
        elastic_resp = json.loads(f.read())

    es_raw = mocker.patch("elasticsearch.connection.Urllib3HttpConnection.perform_request")
    es_raw.side_effect = [
        (200, {}, json.dumps(elastic_resp)),
        (200, {}, json.dumps(elastic_resp)),
    ]

    rv = client.get("/feed/rss?q=blood")
    assert rv.status_code == 200
    assert '<rss version="2.0">' in str(rv.content)

    rv = client.get("/zh/feed/rss?q=blood")
    assert rv.status_code == 200
    assert '<rss version="2.0">' in str(rv.content)


def test_basic_work_landing_page(client: Any, mocker: Any) -> None:
    with open("tests/files/elastic_fulltext_get.json") as f:
        elastic_resp = json.loads(f.read())

    es_raw = mocker.patch("elasticsearch.connection.Urllib3HttpConnection.perform_request")
    es_raw.side_effect = [
        (200, {}, json.dumps(elastic_resp)),
        (200, {}, json.dumps(elastic_resp)),
    ]

    rv = client.get("/work/2x5qvct2dnhrbctqa2q2uyut6a")
    assert rv.status_code == 200
    assert b"citation_pdf_url" in rv.content

    rv = client.get("/zh/work/2x5qvct2dnhrbctqa2q2uyut6a")
    assert rv.status_code == 200
    assert b"citation_pdf_url" in rv.content


def test_basic_access_redirect(client: Any, mocker: Any) -> None:
    with open("tests/files/elastic_fulltext_get.json") as f:
        elastic_resp = json.loads(f.read())

    es_raw = mocker.patch("elasticsearch.connection.Urllib3HttpConnection.perform_request")
    es_raw.side_effect = [
        (200, {}, json.dumps(elastic_resp)),
        (200, {}, json.dumps(elastic_resp)),
    ]

    rv = client.get(
        "/work/2x5qvct2dnhrbctqa2q2uyut6a/access/wayback/https://www.federalreserve.gov/econresdata/feds/2015/files/2015118pap.pdf",
        follow_redirects=False,
    )
    assert rv.status_code == 302
    assert (
        rv.headers["Location"]
        == "https://web.archive.org/web/20200206164725id_/https://www.federalreserve.gov/econresdata/feds/2015/files/2015118pap.pdf"
    )

    # check that URL is validated (force fatcat API fallback to fail)
    fatcat_api_raw = mocker.patch("fatcat_openapi_client.ApiClient.call_api")
    fatcat_api_raw.side_effect = [fatcat_openapi_client.ApiException(status=404, reason="dummy")]
    rv = client.get(
        "/work/2x5qvct2dnhrbctqa2q2uyut6a/access/wayback/https://www.federalreserve.gov/econresdata/feds/2015/files/2015118pap.pdf.DUMMY",
        follow_redirects=False,
    )
    assert rv.status_code == 404


def test_access_redirect_fallback(client: Any, mocker: Any) -> None:
    with open("tests/files/elastic_fulltext_get.json") as f:
        elastic_resp = json.loads(f.read())

    es_raw = mocker.patch("elasticsearch.connection.Urllib3HttpConnection.perform_request")
    es_raw.side_effect = [
        (200, {}, json.dumps(elastic_resp)),
        (200, {}, json.dumps(elastic_resp)),
        (200, {}, json.dumps(elastic_resp)),
        (200, {}, json.dumps(elastic_resp)),
    ]
    fatcat_get_work_raw = mocker.patch("fatcat_openapi_client.DefaultApi.get_work")
    fatcat_get_work_raw.side_effect = [
        fatcat_openapi_client.WorkEntity(
            state="active",
            ident="wwwwwwwwwwwwwwwwwwwwwwwwww",
        )
    ] * 4
    fatcat_get_work_releases_raw = mocker.patch(
        "fatcat_openapi_client.DefaultApi.get_work_releases"
    )
    fatcat_get_work_releases_raw.side_effect = [
        [
            fatcat_openapi_client.ReleaseEntity(
                ident="rrrrrrrrrrrrrrrrrrrrrrrrrr",
                ext_ids=fatcat_openapi_client.ReleaseExtIds(),
            ),
        ]
    ] * 4
    fatcat_get_release_raw = mocker.patch("fatcat_openapi_client.DefaultApi.get_release")
    fatcat_get_release_raw.side_effect = [
        fatcat_openapi_client.ReleaseEntity(
            state="active",
            ident="rrrrrrrrrrrrrrrrrrrrrrrrrr",
            ext_ids=fatcat_openapi_client.ReleaseExtIds(),
            files=[
                fatcat_openapi_client.FileEntity(
                    ident="ffffffffffffffffffffffffff",
                    urls=[
                        fatcat_openapi_client.FileUrl(
                            rel="web",
                            url="https://blarg.example.com",
                        ),
                        fatcat_openapi_client.FileUrl(
                            rel="webarchive",
                            url="https://web.archive.org/web/12345/https://example.com",
                        ),
                        fatcat_openapi_client.FileUrl(
                            rel="archive",
                            url="https://archive.org/download/some/thing.pdf",
                        ),
                    ],
                ),
            ],
        )
    ] * 4

    # redirects should work after API lookup, for both wayback and archive.org
    rv = client.get(
        "/work/2x5qvct2dnhrbctqa2q2uyut6a/access/wayback/https://example.com",
        follow_redirects=False,
    )
    assert rv.status_code == 302
    assert rv.headers["Location"] == "https://web.archive.org/web/12345id_/https://example.com"

    rv = client.get(
        "/work/2x5qvct2dnhrbctqa2q2uyut6a/access/ia_file/some/thing.pdf",
        follow_redirects=False,
    )
    assert rv.status_code == 302
    assert rv.headers["Location"] == "https://archive.org/download/some/thing.pdf"

    # wrong URLs should still not work, but display a page with helpful links
    rv = client.get(
        "/work/2x5qvct2dnhrbctqa2q2uyut6a/access/wayback/https://www.federalreserve.gov/econresdata/feds/2015/files/2015118pap.pdf.DUMMY",
        follow_redirects=False,
    )
    assert rv.status_code == 404
    assert b"Access Location Not Found" in rv.content
    assert b"web.archive.org/web/*/https://www.federalreserve.gov" in rv.content

    rv = client.get(
        "/work/2x5qvct2dnhrbctqa2q2uyut6a/access/ia_file/some/thing.else.pdf",
        follow_redirects=False,
    )
    assert rv.status_code == 404
    assert b"Access Location Not Found" in rv.content
    assert b"archive.org/download/some/thing.else.pdf" in rv.content


@pytest.mark.skip(reason="todo: requires a mocked fatcat API client, not just es")
def test_access_redirect_encoding(client: Any, mocker: Any) -> None:
    with open("tests/files/elastic_get_work_a6gvpil4brdgzhqyaog3ftngqe.json") as f:
        elastic_ia_resp = json.loads(f.read())
    with open("tests/files/elastic_get_work_ao5l3ykgbvg2vfpqe2y5qold5y.json") as f:
        elastic_wayback_resp = json.loads(f.read())

    es_raw = mocker.patch("elasticsearch.connection.Urllib3HttpConnection.perform_request")
    es_raw.side_effect = [
        (200, {}, json.dumps(elastic_ia_resp)),
        (200, {}, json.dumps(elastic_wayback_resp)),
    ]

    # tricky "URL encoding in archive.org path" case
    rv = client.get(
        "/work/a6gvpil4brdgzhqyaog3ftngqe/access/ia_file/crossref-pre-1909-scholarly-works/10.1016%252Fs0140-6736%252802%252912493-7.zip/10.1016%252Fs0140-6736%252802%252912928-x.pdf",
        follow_redirects=False,
    )
    assert rv.status_code == 302
    assert (
        rv.headers["Location"]
        == "https://archive.org/download/crossref-pre-1909-scholarly-works/10.1016%252Fs0140-6736%252802%252912493-7.zip/10.1016%252Fs0140-6736%252802%252912928-x.pdf"
    )

    # spaces ("%20" vs "+")
    rv = client.get(
        "/work/ao5l3ykgbvg2vfpqe2y5qold5y/access/wayback/http://sudjms.net/issues/5-4/pdf/8)A%20comparison%20study%20of%20histochemical%20staining%20of%20various%20tissues%20after.pdf",
        follow_redirects=False,
    )
    assert rv.status_code == 302
    assert (
        rv.headers["Location"]
        == "https://web.archive.org/web/20170811115414id_/http://sudjms.net/issues/5-4/pdf/8)A%20comparison%20study%20of%20histochemical%20staining%20of%20various%20tissues%20after.pdf"
    )
