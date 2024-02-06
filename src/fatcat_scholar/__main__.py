import typer
import uvicorn

from fatcat_scholar.worker import main as worker_main

cli = typer.Typer()

@cli.command()
def web() -> None:
    print("starting web")
    uvicorn.run("fatcat_scholar:app", port=9819)

@cli.command()
def worker() -> None:
    # TODO reimplement as typer interface
    worker_main()

def main() -> None:
    cli()

if __name__ == "__main__":
    main()
