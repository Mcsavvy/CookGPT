from werkzeug.security import check_password_hash, generate_password_hash

from cookgpt.auth.models import JwtTokenMixin
from cookgpt.base import BaseModelMixin
from cookgpt.ext.database import db


class User(db.Model, BaseModelMixin, JwtTokenMixin):  # type: ignore
    """User model"""

    first_name = db.Column(db.String(40), nullable=False)
    last_name = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    username = db.Column(db.String(40), unique=True)
    password = db.Column(db.Text, nullable=False)  # type: ignore
    jwt_tokens = db.relationship(  # type: ignore
        "JwtToken",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @property
    def serializable_keys(self) -> "set[str]":
        """Serializable keys"""
        s_keys: "set[str]" = super().serializable_keys
        return s_keys.union(
            {"first_name", "last_name", "email", "username", "jwt_tokens"}
        )

    @classmethod
    def create(cls, commit=True, **kwargs) -> "User":
        """Creates user model"""
        if "password" in kwargs:
            kwargs["password"] = generate_password_hash(kwargs["password"])
        if (
            "username" in kwargs
            and cls.query.filter_by(username=kwargs["username"]).first()
        ):
            raise cls.CreateError("username is taken")
        if (
            "email" in kwargs
            and cls.query.filter_by(email=kwargs["email"]).first()
        ):
            raise cls.CreateError("email is taken")
        return super().create(commit, **kwargs)

    def update(self, commit=True, **kwargs) -> "User":
        """Updates user model"""
        if "password" in kwargs:
            kwargs["password"] = generate_password_hash(kwargs["password"])
        # if username is used by a different user, raise error
        if (
            "username" in kwargs
            and self.username != kwargs["username"]
            and self.query.filter_by(username=kwargs["username"]).first()
        ):
            raise self.UpdateError("username is taken")
        # if email is used by a different user, raise error
        if (
            "email" in kwargs
            and self.email != kwargs["email"]
            and self.query.filter_by(email=kwargs["email"]).first()
        ):
            raise self.UpdateError("email is taken")
        return super().update(commit, **kwargs)

    def validate_password(self, password):
        """Validates password"""
        return check_password_hash(self.password, password)
