"""User Database Models"""

from typing import cast

from werkzeug.security import check_password_hash, generate_password_hash

from cookgpt.auth.data.enums import UserType
from cookgpt.auth.models.tokens import TokenMixin
from cookgpt.base import BaseModelMixin
from cookgpt.chatbot.models import ThreadMixin
from cookgpt.ext.database import db


def get_max_chat_cost() -> int:
    """get the max chat cost from the app config"""
    from flask import current_app as app

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
    last_name = db.Column(db.String(30), nullable=False)
    user_type = db.Column(
        db.Enum(UserType), nullable=False, default=UserType.PATIENT
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
        self.user_type.value.title()
        self.id.hex[:6]
        return "{}[{}](name={}, email={}, threads={}, tokens={})".format(
            self.user_type.value.title(),
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

    @property
    def total_chat_cost(self):
        """total cost of all messages"""
        return sum(trd.cost for trd in self.threads)  # type: ignore

    def validate_password(self, password):
        """verify that a password can be used to authenticate as this user"""
        return check_password_hash(self.password, password)

    @classmethod
    def create(cls, commit=True, **kwargs) -> "User":
        """create a new user"""

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
        """update a user"""
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
