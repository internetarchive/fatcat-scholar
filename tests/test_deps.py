# TODO delete this test
def test_gunicorn_regression() -> None:
    """
    Had a problem where these two libraries were not included and running
    uvicorn under gunicorn failed.
    """
    import uvloop
    assert(uvloop is not None)

    import httptools
    assert(httptools is not None)
