from datetime import datetime, timedelta, timezone
from typing import Iterable, cast
from uuid import UUID, uuid4

from flask import current_app as app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from sqlalchemy.orm.dynamic import AppenderQuery

from cookgpt.base import BaseModelMixin
from cookgpt.ext.database import db
from cookgpt.utils import utcnow, utcnow_from__ts


class Token(db.Model, BaseModelMixin):  # type: ignore
    """Json Web Token model"""

    serialize_rules = ("-user",)

    access_token = db.Column(db.String(500), nullable=False, unique=True)
    refresh_token = db.Column(db.String(500), nullable=False, unique=True)
    revoked = db.Column(db.Boolean, nullable=False, default=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    user_id = db.Column(db.Uuid, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return "Token[{}](user={}, active={}, revoked={})".format(
            self.id.hex[:6],
            self.user.name,
            "✔" if self.active else "✗",
            "✔" if self.revoked else "✗",
        )

    def refresh(self):
        """refresh access token"""
        access_token = create_access_token(
            self.user_id.hex, additional_claims={"jti": self.id.hex}
        )
        self.update(access_token=access_token)

    def atoken_has_expired(self):
        """Checks if access token has expired"""
        import jwt

        try:
            decode_token(self.access_token)
        except jwt.exceptions.ExpiredSignatureError:
            return True
        return False

    def rtoken_has_expired(self):
        """Checks if refresh token has expired"""
        import jwt

        try:
            decode_token(self.refresh_token)
        except jwt.exceptions.ExpiredSignatureError:
            return True
        return False

    @property
    def atoken_expiry(self):
        """Gets access_token expiry time"""
        decoded = decode_token(self.access_token, allow_expired=True)
        return datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

    @property
    def rtoken_expiry(self):
        """Gets refresh_token expiry time"""
        decoded = decode_token(self.refresh_token, allow_expired=True)
        return datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

    @classmethod
    def create(cls, user_id, commit=True) -> "Token":  # type: ignore
        """Creates jwt token"""
        id = uuid4()
        atoken = create_access_token(
            user_id.hex, additional_claims={"jti": id.hex}
        )
        rtoken = create_refresh_token(
            user_id.hex, additional_claims={"jti": id.hex}
        )
        token = super().create(
            id=id,
            user_id=user_id,
            access_token=atoken,
            refresh_token=rtoken,
            commit=commit,
        )
        return token


class TokenMixin:
    """TokenMixin"""

    tokens: "AppenderQuery[Token]"
    id: "UUID"

    def revoke_all_tokens(self):
        """Revokes all jwt tokens"""
        for token in cast(Iterable[Token], self.tokens):
            token.update(revoked=True, commit=False)
        db.session.commit()

    def revoke_expired_tokens(self):
        """Revokes expired jwt tokens"""
        for token in cast(Iterable[Token], self.tokens):
            if token.atoken_has_expired():
                token.update(revoked=True, commit=False)
        db.session.commit()

    def revoke_token(self, token: "Token"):
        """Revokes jwt token"""
        token.update(revoked=True)

    def deactivate_token(self, token: "Token"):
        """Deactivate jwt token"""
        token.update(active=False)

    def create_token(self):
        """Creates jwt token"""
        token = Token.create(user_id=self.id, commit=True)
        return token

    def get_token(
        self, atoken: "str|None" = None, rtoken: "str|None" = None
    ) -> "Token":
        """Gets jwt token"""
        if not (atoken or rtoken):  # pragma: no cover
            raise ValueError("atoken or rtoken must be supplied")
        if atoken and rtoken:
            return Token.query.filter_by(
                user=self, access_token=atoken, refresh_token=rtoken
            ).first()
        elif atoken:
            return Token.query.filter_by(
                user=self, access_token=atoken
            ).first()
        return Token.query.filter_by(user=self, refresh_token=rtoken).first()

    def get_all_tokens(self) -> "list[Token]":
        """Gets all jwt tokens"""
        return self.tokens  # type: ignore

    def get_active_tokens(self, with_expired=False):
        """Gets active jwt tokens"""
        active_tokens = Token.query.filter_by(
            user=self, active=True, revoked=False
        )
        for token in active_tokens.all():
            if with_expired or not token.atoken_has_expired():
                yield token

    def get_inactive_tokens(self, with_expired=False):
        """Gets expired jwt tokens"""
        inactive_tokens = Token.query.filter_by(
            user=self, active=False, revoked=False
        )
        for token in inactive_tokens.all():
            if with_expired or not token.atoken_has_expired():
                yield token

    def request_token(self) -> "Token":
        """Requests a jwt token"""

        token: "Token"
        leeway: timedelta = app.config["JWT_ACCESS_TOKEN_LEEWAY"]
        active_tokens = Token.query.filter_by(
            user=self, active=True, revoked=False
        ).order_by(Token.created_at.desc())
        for token in active_tokens.all():
            if token.atoken_has_expired():
                # skip expired tokens
                continue
            # check if token is about to expire
            decoded = decode_token(token.access_token)
            exp = utcnow_from__ts(decoded["exp"])
            if exp - leeway >= utcnow():
                return cast(Token, token)
        return self.create_token()
