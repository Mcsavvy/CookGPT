from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from apiflask import APIBlueprint
from flask_jwt_extended import JWTManager

if TYPE_CHECKING:
    from cookgpt.app import App

jwt = JWTManager()
app = APIBlueprint(
    "auth", __name__, url_prefix="/auth", tag="auth", cli_group="auth"
)


@jwt.user_lookup_loader
def user_lookup_loader(header, payload):
    """get authenticated user instance"""
    from cookgpt.user.models import User

    return User.query.filter_by(id=UUID(payload["sub"]))


def init_app(_app: "App"):
    """Initializes extension"""
    access_token_leeway = _app.config.get("JWT_TOKEN_LEEWAY")
    access_token_expires = _app.config.get("JWT_ACCESS_TOKEN_EXPIRES")
    refresh_token_expires = _app.config.get("JWT_REFRESH_TOKEN_EXPIRES")

    if isinstance(access_token_leeway, dict):
        _app.config["JWT_TOKEN_LEEWAY"] = timedelta(**access_token_leeway)
    if isinstance(access_token_expires, dict):
        _app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
            **access_token_expires
        )
    if isinstance(refresh_token_expires, dict):
        _app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(
            **refresh_token_expires
        )
    jwt.init_app(_app)


from cookgpt.auth import cli  # noqa: E402, F401
from cookgpt.auth import views  # noqa: E402, F401
