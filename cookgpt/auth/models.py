from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Iterable, cast
from uuid import UUID, uuid4

from flask import current_app as app
from flask_jwt_extended import create_access_token, decode_token

from cookgpt.base import BaseModelMixin
from cookgpt.ext.database import db

if TYPE_CHECKING:
    from sqlalchemy.orm.dynamic import AppenderQuery


class JwtToken(db.Model, BaseModelMixin):  # type: ignore
    """JwtToken model"""

    access_token = db.Column(db.Text, nullable=False, unique=True)
    revoked = db.Column(db.Boolean, nullable=False, default=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    user_id = db.Column(db.Uuid, db.ForeignKey("user.id"), nullable=False)

    @property
    def serializable_keys(self) -> "set[str]":
        """Serializable keys"""
        s_keys: "set[str]" = super().serializable_keys
        return s_keys.union({"active", "user_id", "revoked", "access_token"})

    @property
    def is_expired(self):
        """Checks if token is expired"""
        import jwt

        try:
            decode_token(self.access_token)
        except jwt.exceptions.ExpiredSignatureError:
            return True
        return False

    @classmethod
    def create(cls, user_id, commit=True) -> "JwtToken":  # type: ignore
        """Creates jwt token"""
        id = uuid4()
        jwt = create_access_token(
            user_id.hex, additional_claims={"jti": id.hex}
        )
        token = super().create(
            id=id, user_id=user_id, access_token=jwt, commit=commit
        )
        return token


class JwtTokenMixin:
    """JwtTokenMixin"""

    jwt_tokens: "AppenderQuery[JwtToken]"
    id: "UUID"

    def revoke_all_jwt_tokens(self):
        """Revokes all jwt tokens"""
        for token in cast(Iterable[JwtToken], self.jwt_tokens):
            token.update(revoked=True, commit=False)
        db.session.commit()

    def revoke_expired_jwt_tokens(self):
        """Revokes expired jwt tokens"""
        for token in cast(Iterable[JwtToken], self.jwt_tokens):
            if token.is_expired:
                token.update(revoked=True, commit=False)
        db.session.commit()

    def revoke_jwt_token(self, token: "JwtToken"):
        """Revokes jwt token"""
        token.update(revoked=True)

    def deactivate_jwt_token(self, token: "JwtToken"):
        """Deactivate jwt token"""
        token.update(active=False)

    def create_jwt_token(self):
        """Creates jwt token"""
        token = JwtToken.create(user_id=self.id, commit=True)
        self.jwt_tokens.append(token)
        return token

    def get_jwt_token(self, value: str):
        """Gets jwt token"""
        return self.jwt_tokens.filter_by(access_token=value).first()

    def get_all_jwt_tokens(self) -> "list[JwtToken]":
        """Gets all jwt tokens"""
        return self.jwt_tokens.all()

    def get_active_jwt_tokens(self, with_expired=False):
        """Gets active jwt tokens"""
        for token in self.jwt_tokens.filter_by(active=True, revoked=False):
            if with_expired or not token.is_expired:
                yield token

    def get_inactive_jwt_tokens(self, with_expired=False):
        """Gets expired jwt tokens"""
        for token in self.jwt_tokens.filter_by(active=False, revoked=False):
            if with_expired or not token.is_expired:
                yield token

    def request_jwt_token(self) -> "JwtToken":
        """Requests a jwt token"""

        leeway: timedelta = app.config["JWT_ACCESS_TOKEN_LEEWAY"]
        for token in (
            self.jwt_tokens.filter_by(revoked=False, active=True)
            .order_by(JwtToken.created_at.desc())
            .all()
        ):
            if token.is_expired:
                # skip expired tokens
                continue
            # check if token is about to expire
            decoded = decode_token(token.access_token)
            exp = datetime.fromtimestamp(decoded["exp"])
            if exp - leeway >= datetime.utcnow():
                return token
        return self.create_jwt_token()
