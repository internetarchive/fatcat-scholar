def test_gunicorn_regression() -> None:
    """
    Had a problem where these two libraries were not included and running
    uvicorn under gunicorn failed.
    """
    import uvloop

    uvloop.__version__
    import httptools

    httptools.__version__
