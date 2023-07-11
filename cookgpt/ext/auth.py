from flask_jwt_extended import JWTManager
from cookgpt.user.models import User  # noqa: F401


def init_app(app):
    """Initializes extension"""
    JWTManager(app)
