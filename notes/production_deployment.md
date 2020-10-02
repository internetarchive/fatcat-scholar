
## FastAPI in Production

Use gunicorn plus uvicorn, to get multiple worker processes, each running
async:

    gunicorn example:app -w 4 -k uvicorn.workers.UvicornWorker
