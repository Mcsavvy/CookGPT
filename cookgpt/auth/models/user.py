"""User Database Models."""

from typing import TYPE_CHECKING, cast

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

# from cookgpt.ext.auth import bcrypt
from werkzeug.security import check_password_hash, generate_password_hash

from cookgpt.auth.data.enums import UserType
from cookgpt.auth.models.tokens import TokenMixin
from cookgpt.chatbot.models import ThreadMixin
from cookgpt.ext.database import db

if TYPE_CHECKING:
    from cookgpt.auth.models.tokens import Token  # noqa: F401
    from cookgpt.chatbot.models import Thread  # noqa: F401


def get_max_chat_cost() -> int:
    """Get the max chat cost from the app config."""
    from cookgpt.globals import current_app as app

    return cast(int, app.config["MAX_CHAT_COST"])


class User(
    db.Model,  # type: ignore
    TokenMixin,
    ThreadMixin,
):
    """An authenticated user."""

    serialize_rules = ("-password",)

    first_name: Mapped[str] = mapped_column(db.String(30))
    last_name: Mapped[str | None] = mapped_column(db.String(30))
    user_type: Mapped[UserType] = mapped_column(
        Enum(UserType), default=UserType.COOK
    )
    username: Mapped[str | None] = mapped_column(db.String(80), unique=True)
    email: Mapped[str] = mapped_column(db.String(120), unique=True)
    password: Mapped[str] = mapped_column(db.String(120))
    tokens: Mapped[list["Token"]] = db.relationship(  # type: ignore
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    max_chat_cost: Mapped[int] = mapped_column(default=get_max_chat_cost)
    threads: Mapped[
        list["Thread"]
    ] = db.relationship(  # type: ignore[assignment]
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        """Get a string representation of the user."""
        return "{}[{}](name={}, email={}, threads={}, tokens={})".format(
            self.type.name,
            self.uid,
            self.name,
            self.email,
            len(self.threads),  # type: ignore
            len(self.tokens),  # type: ignore
        )  # type: ignore

    @property
    def name(self):
        """Get user's name."""
        name = self.first_name
        if self.last_name:
            name += " " + self.last_name
        return name

    @property
    def profile_picture(self):
        """Get the user's profile picture."""
        # hash the user's email to get a gravatar
        from hashlib import sha256

        return (
            "https://www.gravatar.com/avatar/"
            + sha256(self.email.encode()).hexdigest()
        )

    @property
    def type(self) -> UserType:  # pragma: no cover
        """Get the user's type.

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
        """Verify that a password can be used to authenticate as this user."""
        return check_password_hash(self.password, password)
        # return bcrypt.check_password_hash(self.password, password)

    @classmethod
    def create(cls, commit=True, **kwargs) -> "User":
        """Create a new user."""
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
            kwargs["password"] = generate_password_hash(kwargs["password"])
            # kwargs["password"] = bcrypt.generate_password_hash(
            #     kwargs["password"]
            # )
        return super().create(commit, **kwargs)

    def update(self, commit=True, **kwargs) -> "User":
        """Update a user."""
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
            kwargs["password"] = generate_password_hash(kwargs["password"])
            # kwargs["password"] = bcrypt.generate_password_hash(
            # kwargs["password"]
            # )
        return super().update(commit, **kwargs)
