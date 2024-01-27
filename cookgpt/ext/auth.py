"""Authentication extension."""

from typing import TYPE_CHECKING

from apiflask import HTTPTokenAuth
from apiflask.scaffold import _annotate

# from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required
from sentry_sdk import set_user

from cookgpt import docs
from cookgpt.ext.database import db
from cookgpt.utils import cast_func_to

if TYPE_CHECKING:  # pragma: no cover
    from cookgpt.app import App
    from cookgpt.auth.models.user import User


auth = HTTPTokenAuth(description=docs.SECURITY)


jwt = JWTManager()
# bcrypt = Bcrypt()


@cast_func_to(jwt_required)
def auth_required(*args, **kwargs):
    """Decorator for authentication required endpoints."""

    def decorator(fn):
        _annotate(fn, auth=auth, roles=[])
        return jwt_required(*args, **kwargs)(fn)

    return decorator


@jwt.token_verification_loader
def token_verification_callback(header: dict, payload: dict):
    """Verify the authenticity of a token is valid and active.

    Args:
        header (dict): The header of the token.
        payload (dict): The payload of the token.

    Returns: bool
    """
    from uuid import UUID

    from cookgpt.auth.models import Token

    token = db.session.get(Token, UUID(payload["jti"]))
    if token is None:  # pragma: no cover
        return False
    if token.active:
        user: "User" = token.user
        set_user({"id": user.id, "username": user.name, "email": user.email})
        return True
    return False  # pragma: no cover


@jwt.token_in_blocklist_loader
def token_in_blocklist_callback(header: dict, payload: dict):
    """Check if the token is in the blocklist.

    Args:
        header (dict): The token header.
        payload (dict): The token payload.

    Returns:
        bool: True if the token is in the blocklist, False otherwise.
    """
    from uuid import UUID

    from cookgpt.auth.models import Token

    token = db.session.get(Token, UUID(payload["jti"]))
    if token is None:  # pragma: no cover
        return False
    return token.revoked


@jwt.token_verification_failed_loader
def token_verification_failed_callback(
    header: dict, payload: dict
):  # pragma: no cover
    """Token verification failed callback."""
    from flask_jwt_extended.config import config

    from cookgpt.utils import jsonify

    return jsonify({config.error_msg_key: "Token verification failed"}, 422)


@jwt.user_lookup_loader
def user_loader_callback(header, payload):
    """User loader callback."""
    from uuid import UUID

    from cookgpt.auth.models import User

    return db.session.get(User, UUID(payload["sub"]))


def init_app(app: "App"):
    """Initializes extension."""
    jwt.init_app(app)
    # bcrypt.init_app(app)
