"""
    Request handler and decoder.
    Allows to query auth data from your token or request.
    Root handler for authentication decode.
"""

from sqlalchemy.orm import Session
from fastapi import Request

from app.database import crud
from app.services.permissions import Permissions, parse_permissions_from_scope
from app.services.api.errors import ApiErrorCode, ApiErrorException

from app.tokens.access_token import AccessToken
from app.tokens.session_token import SessionToken
from app.tokens._token import _Token
from app.database.models.user import User
from app.database.models.user_session import UserSession

TokenType = SessionToken | AccessToken
class AuthData(object):
    """ DTO for authenticated request."""

    user: User
    token: TokenType
    session: UserSession
    permissions: Permissions | None

    def __init__(self, token: TokenType, session: UserSession, \
        user: User | None = None, permissions: Permissions | None = None) -> None:
        """
            :param user: User database model object.
            :param token: Session or access token object.
            :param session: User session database model object.
        """
        self.user = user
        self.token = token
        self.session = session

        # Parse permission once.
        self.permissions = permissions if permissions else parse_permissions_from_scope(token._scope)


def query_auth_data_from_token(token: str, db: Session, *, \
    only_session_token: bool = False, 
    required_permissions: Permissions | None = None,
    allow_deactivated: bool = False
    ) -> AuthData:
    """
        Queries authentication data from your token.
        :param token: Token itself.
        :param db: Database session.
        :param only_session_token: If true, will query for session token, not access.
        :param required_permissions: If passed, will require permission from token.
        :param allow_deactivated: If true, allow deactivated user to authenticate.
    """

    # Decode external token and query auth data from it.
    token_type = SessionToken if only_session_token else AccessToken
    auth_data = _decode_token(
        token, token_type, db,
        required_permissions=required_permissions
    )
    if only_session_token:
        assert auth_data.token._type == SessionToken._type
    return _query_auth_data(auth_data, db, allow_deactivated)


def query_auth_data_from_request(req: Request, db: Session, *, \
    only_session_token: bool = False, required_permissions: Permissions | None = None, allow_deactivated: bool = False
    ) -> AuthData:
    """
        Queries authentication data from request (from request token).
        :param req: Request itself.
        :param db: Database session.
        :param only_session_token: If true, will query for session token, not access.
        :param required_permissions: If passed, will require permission from token.
        :param allow_deactivated: If true, allow deactivated user to authenticate.
    """

    # Get token from request and query data from it as external token.
    token = _get_token_from_request(req, only_session_token)
    return query_auth_data_from_token(
        token, db, 
        only_session_token=only_session_token, 
        required_permissions=required_permissions, 
        allow_deactivated=allow_deactivated
    )


def _get_token_from_request(req: Request, only_session_token: bool) -> str:
    """
        Returns token from request.
        :param req: Request itself.
        :param only_session_token: If true, will get session token.
    """
    if only_session_token:
        return req.query_params.get("session_token", "")
    return req.headers.get("Authorization", "") or req.query_params.get("access_token", "")


def _decode_token(token: str, token_type: AccessToken | SessionToken, db: Session, \
    required_permissions: Permissions | None = None) -> AuthData:
    """
        Decodes given token, to it payload and session.
        :param token: Token to decode.
        :param token_type: Token type to get.
        :param db: Database session.
        :param required_permissions: If passed, will require permission from token.
    """
    
    if token_type._type not in ("access", "session"):
        raise ValueError("Unexpected type of the token type inside _decode_token!")

    unsigned_token = token_type.decode_unsigned(token)
    session = _query_session_from_sid(unsigned_token.get_session_id(), db)
    signed_token = token_type.decode(token, key=session.token_secret)
    assert signed_token.signature_is_valid()

    # Checks for token allowance.
    scope = signed_token.get_scope() if token_type._type == "access" else ""
    permissions = _query_scope_permissions(scope, required_permissions)

    # Return DTO.
    return AuthData(
        token=signed_token,
        session=session,
        permissions=permissions
    )


def _query_scope_permissions(scope: str, required_permissions: Permissions | None) -> Permissions:
    """
        Queries scope permissions with checking required permission.
        :param scope: Scope string (From request).
        :param required_permissions: Permission to require.
    """
    permissions = parse_permissions_from_scope(scope)

    if required_permissions:
        for required_permission in required_permissions:
            if required_permission not in permissions:
                raise ApiErrorException(
                    ApiErrorCode.AUTH_INSUFFICIENT_PERMISSSIONS, 
                    f"Insufficient permissions (required: {required_permission.value})", 
                    {"required_scope": required_permission.value})

    return permissions


def _query_session_from_sid(session_id: int | None, db: Session) -> UserSession:
    """
        Queries session from SID (session_id).
        :param session_id: SID itself.
        :param db: Database sesion.
    """

    session = crud.user_session.get_by_id(db, session_id=session_id) if session_id else None

    # Validate session.
    if not session:
        raise ApiErrorException(ApiErrorCode.AUTH_INVALID_TOKEN, "Token invalid!")
    if not session.is_active:
        raise ApiErrorException(ApiErrorCode.AUTH_INVALID_TOKEN, "Session closed (Token invalid due to session deactivation)!")

    return session


def _query_auth_data(auth_data: AuthData, \
    db: Session, allow_deactivated: bool) -> AuthData:
    """
        Finalizes query of  authentication data.
        :param auth_data: Authentication data.
        :param session: User session.
        :param db: Database session.
        :param allow_deactivated: If true, allow deactivated user to authenticate.
    """
    user = crud.user.get_by_id(db=db, user_id=auth_data.token.get_subject())

    # Validate authentication data.
    if not user:
        raise ApiErrorException(ApiErrorCode.AUTH_INVALID_CREDENTIALS, "User with given token does not exists!")
    if not allow_deactivated and not user.is_active:
        raise ApiErrorException(ApiErrorCode.USER_DEACTIVATED, "User account deactivated, access denied!")
    if auth_data.session.owner_id != user.id:
        raise ApiErrorException(ApiErrorCode.AUTH_INVALID_TOKEN, "Token session was linked to another user!")
    
    # Return modified DTO.
    auth_data.user = user
    return auth_data