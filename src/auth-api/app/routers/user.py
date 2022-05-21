"""
    User account API router.
    Provides API methods (routes) for working with user account.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.services.permissions import parse_permissions_from_scope, Permission
from app.services.request import query_auth_data_from_request
from app.services.api.response import api_success, api_error
from app.services.api.errors import ApiErrorCode, ApiErrorException
from app.services.serializers.user import serialize_user
from app.database import crud

from app.database.dependencies import get_db, Session


router = APIRouter()


@router.get("/user.getInfo")
async def method_user_get_info(req: Request, db: Session = Depends(get_db)) -> JSONResponse:
    """ Returns user account information. """

    # Authentication, query user.
    user, token_payload, _  = query_auth_data_from_request(req, db)
    permissions = parse_permissions_from_scope(token_payload["scope"])

    if not user.is_active:
        return api_error(ApiErrorCode.USER_DEACTIVATED, "Cannot get user information, due to user account deactivation!")

    return api_success(serialize_user(user, **{
        "include_email": Permission.email in permissions, 
        "include_optional_fields": True,
        "include_private_fields": True,
        "include_profile_fields": True
    }))

@router.get("/user.getProfileInfo")
async def method_user_get_profile_info(req: Request, \
    user_id: int | None = None, username: str | None = None, db: Session = Depends(get_db)) -> JSONResponse:
    """ Returns user account profile information. """

    if user_id is None and username is None:
        return api_error(ApiErrorCode.API_INVALID_REQUEST, "user_id or username required!")
    if user_id is not None and username is not None:
        return api_error(ApiErrorCode.API_INVALID_REQUEST, "Please pass only user_id or username!")
        
    if user_id is not None:
        user = crud.user.get_by_id(db, user_id)
    else:
        user = crud.user.get_by_username(db, username)

    # User.
    if not user:
        return api_error(ApiErrorCode.USER_NOT_FOUND, f"User with requested {'username' if user_id is None else 'id'} was not found!")
    if not user.is_active:
        return api_error(ApiErrorCode.USER_DEACTIVATED, "Unable to get user, due to user account deactivation!")

    # Privacy.
    if not user.privacy_profile_public:
        return api_error(ApiErrorCode.USER_PROFILE_PRIVATE, "Requested user preferred to keep his profile private!")
    if user.privacy_profile_require_auth:
        try:
            query_auth_data_from_request(req, db)
        except ApiErrorException:
            return api_error(ApiErrorCode.USER_PROFILE_AUTH_REQUIRED, "Requested user preferred to show his profile only for authorized users!")
            
    return api_success(serialize_user(user, **{
        "include_email": False,
        "include_optional_fields": True,
        "include_private_fields": False,
        "include_profile_fields": True
    }))

@router.get("/user.getCounters")
async def method_user_get_counter(req: Request, db: Session = Depends(get_db)) -> JSONResponse:
    """ Returns user account counters (Count of different items, like for badges). """
    query_auth_data_from_request(req, db)
    return api_success({
        "oauth_clients": crud.oauth_client.get_count_by_owner_id()
    })


@router.get("/user.setProfileInfo")
async def method_user_set_profile_info(req: Request, db: Session = Depends(get_db)) -> JSONResponse:
    """ Updates user public profile information. """
    query_auth_data_from_request(req, db)
    return api_error(ApiErrorCode.API_NOT_IMPLEMENTED, "Updating public profile information is not implemented yet!")


@router.get("/user.setInfo")
async def method_user_set_info(req: Request, \
    first_name: str | None = None, last_name: str | None = None, sex: bool | None = None, avatar_url: str | None = None, \
    db: Session = Depends(get_db)) -> JSONResponse:
    """ Updates user account information. """

    user = query_auth_data_from_request(req, db)[0]
    
    is_updated = False
    if first_name is not None and first_name != user.first_name:
        user.first_name = first_name
        is_updated = True
    if last_name is not None and last_name != user.last_name:
        user.last_name = last_name
        is_updated = True
    if sex is not None and sex != user.sex:
        user.sex = sex
        is_updated = True
    if avatar_url is not None and avatar_url != user.avatar:
        user.avatar = avatar_url
        is_updated = True

    if is_updated:
        db.commit()

    return api_success({
        **serialize_user(user, **{
            "include_email": False, 
            "include_optional_fields": False,
            "include_private_fields": True
        }),
        "updated": is_updated
    })
