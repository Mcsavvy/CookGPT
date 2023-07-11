from flask_jwt_extended import JWTManager
from werkzeug.security import check_password_hash, generate_password_hash

from cookgpt.ext.database import db
from cookgpt.user.models import User


def init_app(app):
    """Initializes extension"""
    JWTManager(app)
