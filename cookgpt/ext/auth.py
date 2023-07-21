from datetime import timedelta
from typing import TYPE_CHECKING

from flask_jwt_extended import JWTManager

from cookgpt.user.models import User

if TYPE_CHECKING:
    from cookgpt.app import App


jwt = JWTManager()


@jwt.user_lookup_loader
def user_loader_callback(header, payload):
    """User loader callback"""
    from uuid import UUID

    return User.query.get(UUID(payload["sub"]))


def init_app(app: "App"):
    """Initializes extension"""
    access_token_leeway = app.config.get("JWT_ACCESS_TOKEN_LEEWAY")
    access_token_expires = app.config.get("JWT_ACCESS_TOKEN_EXPIRES")
    refresh_token_expires = app.config.get("JWT_REFRESH_TOKEN_EXPIRES")

    if isinstance(access_token_leeway, dict):
        app.config["JWT_ACCESS_TOKEN_LEEWAY"] = timedelta(
            **access_token_leeway
        )
    if isinstance(access_token_expires, dict):
        app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
            **access_token_expires
        )
    if isinstance(refresh_token_expires, dict):
        app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(
            **refresh_token_expires
        )
    jwt.init_app(app)
