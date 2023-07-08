"""
    Exception handlers as functions.
    
    Handler is a function 
    that called when there as an exception 
    and should return response.
"""

from fastapi import Response
from app.services.api.response import api_error
from app.services.api.errors import ApiErrorException, ApiErrorCode
from app.config import get_logger


async def validation_exception_handler(_, exception) -> Response:
    """
    Handles plain FastAPI exception (Pydantic internal)
    that is caused by validation error for the request.
    TODO: Better exception formatting to the user / developer.
    """
    return api_error(
        ApiErrorCode.API_INVALID_REQUEST,
        "Invalid request! No further information.",
        {"raw_exception": str(exception)},
    )


async def too_many_requests_handler(_, exception):
    """
    Handles error when user sends too many requests.
    Retry after is number of seconds after which limiter will be reseted.
    """

    retry_after = int(exception.headers["Retry-After"])
    return api_error(
        ApiErrorCode.API_TOO_MANY_REQUESTS,
        f"Too many requests! You are sending requests too fast. Try again in {retry_after}s!",
        {"retry-after": retry_after},
        headers=exception.headers,
    )


async def api_error_exception_handler(_, e: ApiErrorException):
    """
    Custom wrapper for the custom exception.
    Exception is used when there is no way to return response from the function.
    """
    get_logger().debug(
        f"[user][api] Handled API_EXCEPTION with code '{e.api_code}' and message '{e.message}'!"
    )
    return api_error(e.api_code, e.message, e.data, headers=None)


async def not_found_handler(_, __):
    """
    Handler for simple not found FastAPI error.
    """
    return api_error(
        ApiErrorCode.API_METHOD_NOT_FOUND,
        "Method or path not found! Please read documentation.",
    )


async def method_not_allowed(_, __):
    """
    User is tried to use not allowed HTTP method.
    """
    return api_error(
        ApiErrorCode.API_METHOD_NOT_ALLOWED,
        "HTTP method is not allowed! Please read documentation.",
    )


async def internal_server_error_handler(_, __):
    """
    Handler for any other exception that is not handled.
    """
    return api_error(
        ApiErrorCode.API_INTERNAL_SERVER_ERROR,
        "Internal server error! Server is unavailable at this time. Please try again later.",
    )


async def token_wrong_type_error_handler(_, __):
    """
    Auth system catched that token of the user has wrong type.
    Please dive into the auth system .
    """
    return api_error(
        ApiErrorCode.AUTH_INVALID_TOKEN,
        "Token has wrong type! Please read documentation.",
    )


async def token_expired_error_handler(_, __):
    """
    Auth system catched that token of the user has expired.
    """
    return api_error(
        ApiErrorCode.AUTH_EXPIRED_TOKEN,
        "Token has been expired or revoked! Please get new fresh token.",
    )


async def token_invalid_signature_error_handler(_, __):
    """
    Auth system catched that token of the user has invalid signature.
    (Means user mostly tried to self-sign token or corrupted token).
    """
    return api_error(
        ApiErrorCode.AUTH_INVALID_TOKEN,
        "Token has invalid signature! Server is unable to verify that token signed by himself.",
    )


async def token_invalid_error_handler(_, __):
    """
    Auth system catched that token is invalid (any most caused error).
    This is wide exception.
    """
    return api_error(
        ApiErrorCode.AUTH_INVALID_TOKEN, "Token invalid! No additonal information."
    )
