from apiflask import APIBlueprint

from .models import User  # noqa: F401

app = APIBlueprint(
    "userview", __name__, url_prefix="/user", tag="user", cli_group="user"
)


def init_app(_app):
    """Initializes application"""
    _app.register_blueprint(app)


import cookgpt.user.cli  # noqa: E402, F401
