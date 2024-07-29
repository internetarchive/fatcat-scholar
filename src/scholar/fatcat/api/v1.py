from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from fatcat_openapi_client import DefaultApi

from scholar.depends import Ident, fcclient

routes = APIRouter(prefix="/v1")

@routes.get("/", include_in_schema=False)
async def index() -> RedirectResponse:
    return RedirectResponse("/docs", status_code=301)

# TODO the container entities as defined in the openapi generated client are
# not pydantic types and as such can't be used as response types here -- that
# is unfortunate. I don't mind doing that translation but I don't think I'll
# have time until after Force11. I might; but I'll first focus on figuring out
# the subset of routes I want then decide how much time is leftover.
# TODO why no get_container_releases in original?
# TODO evaluate v0 supported for ?expand and ?hide

@routes.get("/get_release/{ident}")
async def get_release(
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        ident: Ident) -> dict[str, Any]:
    return fcclient.get_release(ident).to_dict()

@routes.get("/get_release_files/{ident}")
async def get_release_files(
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        ident: Ident) -> list[dict[str, Any]]:
    return [f.to_dict() for f in fcclient.get_release_files(ident)]

@routes.get("/lookup_release")
async def lookup_release(
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        extid_type:  Annotated[
            str,
            Query(pattern="^doi|wikidata_qid|pmid|pmcid|isbn13|jstor|arxiv|core|ark|mag|oai|hdl$")],
        extid_value: str) -> dict[str, Any]:

    return fcclient.lookup_release(**{extid_type: extid_value.strip()}).to_dict()

@routes.get("/get_work/{ident}")
async def get_work(
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        ident: Ident) -> dict[str, Any]:
    return fcclient.get_work(ident).to_dict()

@routes.get("/get_work_releases/{ident}")
async def get_work_releases(
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        ident: Ident) -> list[dict[str, Any]]:
    return [r.to_dict() for r in fcclient.get_work_releases(ident)]

@routes.get("/get_file/{ident}")
async def get_file(
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        ident: Ident) -> dict:
    return fcclient.get_file(ident).to_dict()

@routes.get("/lookup_file")
async def lookup_file(
        # TODO expand, hide
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        extid_type:  Annotated[
            str, Query(pattern="^md5|sha1|sha256$")],
        extid_value: str) -> dict[str, Any]:
    return fcclient.lookup_file(**{extid_type: extid_value.strip()}).to_dict()

@routes.get("/get_container/{ident}")
async def get_container(
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        ident: Ident) -> dict:
    return fcclient.get_container(ident).to_dict()

@routes.get("/lookup_container")
async def lookup_container(
        # TODO expand, hide
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        extid_type:  Annotated[
            str, Query(pattern="^issnl|issne|issnp|issn|wikidata_qid$")],
        extid_value: str) -> dict[str, Any]:
    return fcclient.lookup_container(**{extid_type: extid_value.strip()}).to_dict()

@routes.get("/get_creator/{ident}")
async def get_creator(
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        ident: Ident) -> dict[str, Any]:
    return fcclient.get_creator(ident).to_dict()

@routes.get("/get_creator_releases/{ident}")
async def get_creator_releases(
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        ident: Ident) -> list[dict[str, Any]]:
    return [r.to_dict() for r in fcclient.get_creator_releases(ident)]

@routes.get("/lookup_creator")
async def lookup_creator(
        # TODO expand, hide
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        extid_type:  Annotated[
            str, Query(pattern="^orcid|wikidata_qid$")],
        extid_value: str) -> dict[str, Any]:
    return fcclient.lookup_creator(**{extid_type: extid_value.strip()}).to_dict()

@routes.get("/get_changelog")
async def get_changelog(
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        limit: int|None) -> list[dict[str, Any]]:
    return [e.to_dict() for e in fcclient.get_changelog(limit=limit)]

@routes.get("/get_changelog_entry/{index}")
async def get_changelog_entry(
        fcclient: Annotated[DefaultApi, Depends(fcclient)],
        index: int) -> dict[str, Any]:
    return fcclient.get_changelog_entry(index).to_dict()


# nice to have

# TODO container model
# TODO release model
# TODO creator model
# TODO file model

# TODO get_release_filesets
# TODO get_release_webcaptures
# TODO get_release_redirects
# TODO get_work_redirects
# TODO get_creator_redirects
# TODO get_file_redirects
# TODO get_container_redirects
# TODO get_fileset
# TODO get_fileset_redirects
# TODO get_webcapture
# TODO get_webcapture_redirects
