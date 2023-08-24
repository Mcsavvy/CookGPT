from typing import TYPE_CHECKING, Optional

from apiflask import HTTPTokenAuth
from apiflask.scaffold import _annotate
from flask_jwt_extended import JWTManager, jwt_required

from cookgpt import docs
from cookgpt.ext.database import db

if TYPE_CHECKING:  # pragma: no cover
    from cookgpt.app import App


auth = HTTPTokenAuth(description=docs.SECURITY)


jwt = JWTManager()


def auth_required(
    optional: bool = False,
    fresh: bool = False,
    refresh: bool = False,
    locations: Optional["str | list"] = None,
    verify_type: bool = True,
    skip_revocation_check: bool = False,
):
    """Protect routes"""

    def decorator(fn):
        _annotate(fn, auth=auth, roles=[])
        return jwt_required(
            optional=optional,
            fresh=fresh,
            refresh=refresh,
            locations=locations,
            verify_type=verify_type,
            skip_revocation_check=skip_revocation_check,
        )(fn)

    return decorator


@jwt.user_lookup_loader
def user_loader_callback(header, payload):
    """User loader callback"""
    from uuid import UUID

    from cookgpt.auth.models import User

    return db.session.get(User, UUID(payload["sub"]))


"""NOTE: For cookie-based authentication

def refresh_expiring_jwts(response):
    '''Refreshes expiring JWTs'''
    from flask_jwt_extended import set_access_cookies
    from cookgpt.auth.models import Token
    from uuid import UUID
    from flask import current_app as app

    jwt = get_jwt()
    if jwt["type"] == "refresh":
        return response
    token: "Token" = db.session.get(Token, UUID(jwt["jti"]))
    if token is None:
        # TODO: Log this
        return response
    expiry = jwt["exp"]
    now = datetime.datetime.now()
    target_timestamp = datetime.datetime.timestamp(
        now + app.config["JWT_REFRESH_TOKEN_LEEWAY"])
    if expiry < target_timestamp:
        token.refresh()
        set_access_cookies(response, token.access_token)
    return response

"""


def init_app(app: "App"):
    """Initializes extension"""
    jwt.init_app(app)
