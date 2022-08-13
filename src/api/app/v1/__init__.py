"""
    API version 1.
    Provides endpoints with logic for `v1` version of the API.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from .endpoints import get_api_routers


def include_api_v1_routers(app: FastAPI) -> None:
    """
    Includes FastAPI API routers to the FastAPI application.
    Will include all endpoint routers of the `v1` version.
    """
    settings = get_settings()
    prefix = f"/v1{settings.proxy_url_prefix}"

    for router in get_api_routers():
        app.include_router(
            router,
            prefix=prefix,
            deprecated=False,
            include_in_schema=True,
            default_response_class=JSONResponse,
        )
