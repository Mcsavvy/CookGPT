"""User Database Models"""

from typing import TYPE_CHECKING, List, Optional, cast

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from cookgpt.auth.data.enums import UserType
from cookgpt.auth.models.tokens import TokenMixin
from cookgpt.chatbot.models import ThreadMixin
from cookgpt.ext.auth import bcrypt
from cookgpt.ext.database import db

if TYPE_CHECKING:
    from cookgpt.auth.models.tokens import Token  # noqa: F401
    from cookgpt.chatbot.models import Thread  # noqa: F401


def get_max_chat_cost() -> int:
    """get the max chat cost from the app config"""
    from cookgpt.globals import current_app as app

    return cast(int, app.config["MAX_CHAT_COST"])


class User(
    db.Model,  # type: ignore
    TokenMixin,
    ThreadMixin,
):
    """An authenticated user"""

    serialize_rules = ("-password",)

    first_name: Mapped[str] = mapped_column(db.String(30))
    last_name: Mapped[Optional[str]] = mapped_column(db.String(30))
    user_type: Mapped[UserType] = mapped_column(
        Enum(UserType), default=UserType.COOK
    )
    username: Mapped[Optional[str]] = mapped_column(db.String(80), unique=True)
    email: Mapped[str] = mapped_column(db.String(120), unique=True)
    password: Mapped[str] = mapped_column(db.String(120))
    tokens: Mapped[List["Token"]] = db.relationship(  # type: ignore
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="Thread.created_at.desc()",
    )

    max_chat_cost: Mapped[int] = mapped_column(default=get_max_chat_cost)
    threads: Mapped[
        List["Thread"]
    ] = db.relationship(  # type: ignore[assignment]
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return "{}[{}](name={}, email={}, threads={}, tokens={})".format(
            self.type.name,
            self.sid[:6],
            self.name,
            self.email,
            len(self.threads),  # type: ignore
            len(self.tokens),  # type: ignore
        )  # type: ignore

    @property
    def name(self):
        """get user's name"""
        name = self.first_name
        if self.last_name:
            name += " " + self.last_name
        return name

    @property
    def profile_picture(self):
        """get the user's profile picture"""
        # hash the user's email to get a gravatar
        from hashlib import sha256

        return (
            "https://www.gravatar.com/avatar/"
            + sha256(self.email.encode()).hexdigest()
        )

    @property
    def type(self) -> UserType:  # pragma: no cover
        """
        get the user's type

        BUG: this is a workaround for a bug where user_type was returned as
             a string instead of an enum
        """
        if not self.user_type:
            return UserType.COOK
        elif isinstance(self.user_type, str):
            return UserType[self.user_type.upper()]
        else:
            return self.user_type

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
            # if password is being updated, hash it
            kwargs["password"] = bcrypt.generate_password_hash(
                kwargs["password"]
            )
        return super().update(commit, **kwargs)
