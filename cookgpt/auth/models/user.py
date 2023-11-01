"""User Database Models"""

from typing import cast

from cookgpt.auth.data.enums import UserType
from cookgpt.auth.models.tokens import TokenMixin
from cookgpt.base import BaseModelMixin
from cookgpt.chatbot.models import ThreadMixin
from cookgpt.ext.auth import bcrypt
from cookgpt.ext.database import db


def get_max_chat_cost() -> int:
    """get the max chat cost from the app config"""
    from cookgpt.globals import current_app as app

    return cast(int, app.config["MAX_CHAT_COST"])


class User(
    BaseModelMixin,
    db.Model,  # type: ignore
    TokenMixin,
    ThreadMixin,
):
    """An authenticated user"""

    serialize_rules = ("-password",)

    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=True)
    user_type = db.Column(
        db.Enum(UserType), nullable=False, default=UserType.COOK
    )
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    tokens = db.relationship(  # type: ignore
        "Token",
        backref=db.backref("user"),
        lazy=True,
        cascade="all, delete-orphan",
    )

    max_chat_cost = db.Column(
        db.Integer, nullable=False, default=get_max_chat_cost
    )
    threads = db.relationship(
        "Thread",
        backref=db.backref("user"),
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        "Admin[45g56](name=Dave, email=dave@ex.com, threads=9, token=5)"
        (self.username or self.first_name).title()
        self.get_type().title()
        self.id.hex[:6]
        return "{}[{}](name={}, email={}, threads={}, tokens={})".format(
            self.get_type().title(),
            self.id.hex[:6],
            self.name,
            self.email,
            len(self.threads),  # type: ignore
            len(self.tokens),  # type: ignore
        )  # type: ignore

    @property
    def name(self):
        """get user's name"""
        return (self.username or self.first_name).title()

    def validate_password(self, password):
        """verify that a password can be used to authenticate as this user"""
        return bcrypt.check_password_hash(self.password, password)

    @classmethod
    def create(cls, commit=True, **kwargs) -> "User":
        """create a new user"""

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
        if "password" in kwargs:
            kwargs["password"] = bcrypt.generate_password_hash(
                kwargs["password"]
            )
        return super().create(commit, **kwargs)

    def update(self, commit=True, **kwargs) -> "User":
        """update a user"""
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
        if "password" in kwargs:
            kwargs["password"] = bcrypt.generate_password_hash(
                kwargs["password"]
            )
        return super().update(commit, **kwargs)

    def get_type(self) -> str:  # pragma: no cover
        """
        get the user's type

        NOTE: this is a workaound for a bug where user_type was returned as
              a string instead of an enum
        """
        try:
            return self.user_type.value
        except AttributeError:
            return self.user_type or "cook"
