def test_static_routes(client):
    for route in ("/cat", "/cat/about"):
        rv = client.get(route)
        assert rv.status_code == 200

    assert client.get("/cat/search", follow_redirects=False).status_code == 302
    assert client.get("/static/bogus/route").status_code == 404
