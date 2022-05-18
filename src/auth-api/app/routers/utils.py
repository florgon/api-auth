"""
    Utils API router.
    Provides API methods (routes) for working some utils stuff.
"""

from time import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.api.response import api_success
router = APIRouter()

@router.get("/utils.getServerTime")
async def method_utils_get_server_time() -> JSONResponse:
    """ Authenticates user and gives new session token for user. """

    return api_success({
        "server_time": time()
    })
