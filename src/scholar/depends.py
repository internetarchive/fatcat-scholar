from typing import Annotated, TypeAlias

from fastapi import Path
import fatcat_openapi_client as fcapi
from fatcat_openapi_client import DefaultApi

from scholar.config import settings

Ident: TypeAlias = Annotated[str, Path(min_length=26, max_length=26)]

async def fcclient() -> DefaultApi:
    fc_conf = fcapi.Configuration()
    fc_conf.host = settings.FATCAT_API_HOST
    return DefaultApi(fcapi.ApiClient(fc_conf))

