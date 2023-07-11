from werkzeug.security import check_password_hash, generate_password_hash

from cookgpt.base import BaseModelMixin
from cookgpt.ext.database import db


class User(db.Model, BaseModelMixin):  # type: ignore
    """User model"""

    first_name = db.Column(db.String(40), nullable=False)
    last_name = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    username = db.Column(db.String(40), unique=True)
    password = db.Column(db.Text, nullable=False)

    @classmethod
    def create(cls, commit=True, **kwargs) -> "User":
        """Creates user model"""
        if "password" in kwargs:
            kwargs["password"] = generate_password_hash(kwargs["password"])
        return super().create(commit, **kwargs)

    def update(self, commit=True, **kwargs) -> "User":
        """Updates user model"""
        if "password" in kwargs:
            kwargs["password"] = generate_password_hash(kwargs["password"])
        return super().update(commit, **kwargs)

    def validate_password(self, password):
        """Validates password"""
        return check_password_hash(self.password, password)
