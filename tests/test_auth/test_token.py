"""tests for Token model and TokenMixin."""

from collections.abc import Callable
from datetime import timedelta
from time import sleep
from uuid import UUID

from flask_jwt_extended import decode_token

from cookgpt.auth.models import Token, User
from cookgpt.ext.database import db
from tests.utils import mock_config


class TestTokenModel:
    """Test Token model."""

    def test_create(self, user: "User"):
        """Test create."""
        token = Token.create(user_id=user.id)
        assert token.id is not None
        assert token.user_id == user.id
        assert token.access_token is not None
        assert token.revoked is False
        assert token.active is True

    def test_access_token_created_before_model_is_committed(
        self, user: "User"
    ):
        """Test access token is created before model is saved to database."""
        token = Token.create(user_id=user.id, commit=False)
        assert token.access_token is not None

    def test_token_id_matches_jti(self, user: "User"):
        """Test that JtwToken.id matches the identity in the access_token."""
        token = Token.create(user_id=user.id, commit=True)
        payload = decode_token(token.access_token)
        assert token.id == UUID(payload["jti"])

    def test_convert_jti_to_token(self, user: "User"):
        """Test jti conversion to token."""
        tk1 = Token.create(user_id=user.id, commit=True)
        payload = decode_token(tk1.access_token)
        tk2 = db.session.get(Token, UUID(payload["jti"]))

        assert tk2 == tk1

    def test_to_dict(self, user: "User"):
        """Test to_dict method."""
        keys = [
            "id",
            "user_id",
            "access_token",
            "revoked",
            "active",
            "created_at",
            "updated_at",
        ]
        token = Token.create(user_id=user.id, commit=False)
        dict = token.to_dict()
        for key in keys:
            assert key in dict, f"{key} not in dict"

    def test_atoken_has_expired(self, config, user: "User"):
        """Test that access token has expired."""
        with mock_config(
            config, JWT_ACCESS_TOKEN_EXPIRES=timedelta(seconds=0.1)
        ):
            token1 = user.create_token()
        sleep(0.1)
        assert token1.atoken_has_expired()
        token2 = user.create_token()
        sleep(0.1)
        assert token2.atoken_has_expired() is False

    def test_rtoken_has_expired(self, config, user: "User"):
        """Test that refresh token has expired."""
        with mock_config(
            config, JWT_REFRESH_TOKEN_EXPIRES=timedelta(seconds=0.1)
        ):
            token = user.create_token()
        sleep(0.1)
        assert token.rtoken_has_expired()
        token2 = user.create_token()
        sleep(0.1)
        assert token2.rtoken_has_expired() is False

    def test_refresh(self, user: "User", add_jwt_salt: Callable[[], None]):
        """Test that a token properly refreshes."""
        token = user.create_token()
        atoken = token.access_token
        rtoken = token.refresh_token
        add_jwt_salt()  # add salt so the test passes
        token.refresh()
        db.session.refresh(token)
        assert atoken != token.access_token, "access token not changed"
        assert rtoken == token.refresh_token, "refresh token changed"


class TestTokenMixin:
    """Test TokenMixin."""

    def test_revoke_all_tokens(self, user: "User"):
        """Test revoking all access tokens."""
        # Create some Access tokens for the user
        token1 = Token.create(user_id=user.id, commit=False)
        token2 = Token.create(user_id=user.id, commit=False)
        token3 = Token.create(user_id=user.id, commit=False)
        user.tokens.extend([token1, token2, token3])  # type: ignore
        db.session.commit()

        # Revoke all Access tokens
        user.revoke_all_tokens()

        # Check that all Access tokens are revoked
        for token in user.get_all_tokens():
            assert token.revoked is True, "Token is not revoked"

    def test_revoke_expired_tokens(self, user: "User", config):
        """Test revoking expired access tokens."""
        # Create some Access tokens for the user
        token1 = Token.create(user_id=user.id, commit=False)
        with mock_config(
            config, JWT_ACCESS_TOKEN_EXPIRES=timedelta(seconds=0.1)
        ):
            token2 = Token.create(user_id=user.id, commit=False)
            token3 = Token.create(user_id=user.id, commit=False)

        user.tokens.extend([token1, token2, token3])  # type: ignore
        db.session.commit()

        # Wait for the Access token to expire
        sleep(0.1)

        # Revoke expired Access tokens
        user.revoke_expired_tokens()

        # Check that only the expired Access token is revoked
        assert token1.revoked is False, "Token revoked"
        assert token2.revoked is True, "Token not revoked"
        assert token3.revoked is True, "Token not revoked"

    def test_revoke_token(self, user: "User"):
        """Test revoking access token."""
        # Create a Access token for the user
        token = Token.create(user_id=user.id, commit=False)
        user.tokens.append(token)  # type: ignore
        db.session.commit()

        # Revoke the Access token
        user.revoke_token(token)

        # Check that the Access token is revoked
        assert token.revoked is True

    def test_deactivate_token(self, user: "User"):
        """Test deactivating access token."""
        # Create a Access token for the user
        token = Token.create(user_id=user.id, commit=False)
        user.tokens.append(token)  # type: ignore
        db.session.commit()

        # Deactivate the Access token
        user.deactivate_token(token)

        # Check that the Access token is deactivated
        assert token.active is False

    def test_create_token(self, user: "User"):
        """Test creating access token."""
        # Create a Access token for the user
        token = user.create_token()

        # Check that the Access token is created
        assert token.id is not None
        assert token.user_id == user.id
        assert token.access_token is not None
        assert token.revoked is False
        assert token.active is True

    def test_get_token(self, user: "User"):
        """Test getting access token."""
        # Create a Access token for the user
        token = Token.create(user_id=user.id, commit=False)
        user.tokens.append(token)  # type: ignore
        db.session.commit()

        # Get the token
        tk1 = user.get_token(token.access_token)
        tk2 = user.get_token(token.access_token, token.refresh_token)
        tk3 = user.get_token(None, token.refresh_token)

        assert tk1 == tk2
        assert tk2 == tk3

        # Check that the retrieved Access token is correct
        assert tk1 is not None
        assert tk1.id == token.id
        assert tk1.user_id == user.id
        assert tk1.access_token == token.access_token
        assert tk1.revoked == token.revoked
        assert tk1.active == token.active

    def test_get_all_tokens(self, user: "User"):
        """Test getting all access tokens."""
        # Create some Access tokens for the user
        token1 = Token.create(user_id=user.id, commit=False)
        token2 = Token.create(user_id=user.id, commit=False)
        token3 = Token.create(user_id=user.id, commit=False)
        user.tokens.extend([token1, token2, token3])  # type: ignore
        db.session.commit()

        # Get all Access tokens
        tokens = user.get_all_tokens()

        # Check that all Access tokens are retrieved
        assert len(tokens) == 3
        assert token1 in tokens
        assert token2 in tokens
        assert token3 in tokens

    def test_get_active_tokens(self, user: "User", config):
        """Test getting active access tokens."""
        # Create some Access tokens for the user
        token1 = Token.create(user_id=user.id, commit=False)

        # Expire one of the Access tokens
        with mock_config(
            config, JWT_ACCESS_TOKEN_EXPIRES=timedelta(seconds=0.1)
        ):
            token2 = Token.create(user_id=user.id, commit=False)

        token3 = Token.create(user_id=user.id, commit=False)

        user.tokens.extend([token1, token2, token3])  # type: ignore
        db.session.commit()

        # Deactivate one of the Access tokens
        user.deactivate_token(token3)

        # Wait for token to expire
        sleep(0.1)

        # Get active Access tokens
        tokens = list(user.get_active_tokens())

        # Check that only the active Access tokens are retrieved
        assert len(tokens) == 1
        assert token1 in tokens, "Active token must be enlisted"
        assert token2 not in tokens, (
            "Expired token cannot be listed as "
            "active except with_expired is True"
        )
        assert token3 not in tokens, "Deactivated token cannot be active"

    def test_get_inactive_tokens(self, user: "User", config):
        """Test getting inactive access tokens."""
        # Create some Access tokens for the user
        token1 = Token.create(user_id=user.id, commit=False)

        # Expire one of the Access tokens
        with mock_config(
            config, JWT_ACCESS_TOKEN_EXPIRES=timedelta(seconds=0.1)
        ):
            token2 = Token.create(user_id=user.id, commit=False)

        token3 = Token.create(user_id=user.id, commit=False)

        user.tokens.extend([token1, token2, token3])  # type: ignore
        db.session.commit()

        # Deactivate one of the Access tokens
        user.deactivate_token(token3)

        # Wait for token to expire
        sleep(0.1)

        # Get active Access tokens
        tokens = list(user.get_inactive_tokens())

        # Check that only the active Access tokens are retrieved
        assert len(tokens) == 1
        assert token1 not in tokens, "Active token cannot be inactive"
        assert token2 not in tokens, (
            "Expired token cannot be listed as "
            "inactive except with_expired is True"
        )
        assert token3 in tokens, "Inactivate token must be enlisted"

    def test_request_token(self, user: "User", app):
        """Test requesting a access token."""
        # Create Access tokens
        token1 = user.create_token()
        token2 = user.create_token()

        # request for a token
        token = user.request_token()

        # check that an existing token was returned
        assert token.id == token2.id
        assert token.user_id == user.id
        assert token.access_token == token2.access_token
        assert token.revoked is False
        assert token.active is True

        # Create a new token with a shorter expiry time
        with mock_config(
            app.config, JWT_ACCESS_TOKEN_EXPIRES=timedelta(seconds=0.1)
        ):
            token3 = user.create_token()

        # wait for token to expire
        sleep(0.1)

        # request for another token
        token = user.request_token()

        # check that an existing token was returned
        assert token.id == token2.id
        assert token.user_id == user.id
        assert token.access_token == token2.access_token
        assert token.revoked is False
        assert token.active is True

        # deactivate a token
        user.deactivate_token(token1)

        # revoke a token
        user.revoke_token(token2)

        # request for a new token
        token = user.request_token()

        # check that a new token ws created an return
        assert token not in [
            token1,
            token2,
            token3,
        ], "can't reissue expired, inactive or revoked token"
        assert token.id is not None
        assert token.user_id == user.id
        assert token.access_token is not None
        assert token.revoked is False
        assert token.active is True
