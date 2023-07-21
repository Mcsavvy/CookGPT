from datetime import timedelta
from time import sleep

import pytest
from flask import current_app as app

from cookgpt.auth.models import JwtToken
from cookgpt.ext.database import db
from cookgpt.user.models import User
from tests import random_user, update_config


class TestUserModel:
    """Test user model"""

    def test_create_user(self, user: "User"):
        """Test creating a user"""
        assert user.id is not None
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.email == "johndoe@example.com"
        assert user.username == "johndoe"
        assert user.password != "JohnDoe1234", "Password should be hashed"

    def test_to_dict(self, user: "User"):
        """Test to_dict method"""
        keys = [
            "id",
            "first_name",
            "last_name",
            "email",
            "username",
            "created_at",
            "updated_at",
        ]
        dict = user.to_dict()
        for key in keys:
            assert key in dict, f"{key} not in dict"

    @pytest.mark.usefixtures("app")
    def test_create_user_with_same_username(self):
        """Test creating a user with the same username"""
        user = random_user()
        with pytest.raises(User.CreateError) as excinfo:
            random_user(username=user.username)
        excinfo.match("username is taken")

    @pytest.mark.usefixtures("app")
    def test_create_user_with_same_email(self):
        """Test creating a user with the same email"""
        user = random_user()
        with pytest.raises(User.CreateError) as excinfo:
            random_user(email=user.email)
        excinfo.match("email is taken")

    def test_update_user(self, user: "User"):
        """Test updating a user"""
        user.update(first_name="Jane", password="JaneDoe1234")
        assert user.first_name == "Jane"
        assert user.password != "JaneDoe1234", "Password should be hashed"
        assert user.username == "johndoe", "Username should not be updated"
        assert (
            user.email == "johndoe@example.com"
        ), "Email should not be updated"
        assert user.last_name == "Doe", "Last name should not be updated"

    @pytest.mark.usefixtures("app")
    def test_update_user_with_same_username(self):
        """Test updating a user with the same username"""
        user = random_user()
        user2 = random_user()
        with pytest.raises(User.UpdateError) as excinfo:
            user2.update(username=user.username)
        excinfo.match("username is taken")
        user.update(username=user.username)
        assert True, "Should not raise error"

    @pytest.mark.usefixtures("app")
    def test_update_user_with_same_email(self):
        """Test updating a user with the same email"""
        user = random_user()
        user2 = random_user()
        with pytest.raises(User.UpdateError) as excinfo:
            user2.update(email=user.email)
        excinfo.match("email is taken")
        user.update(email=user.email)
        assert True, "Should not raise error"

    def test_validate_password(self, user: "User"):
        """Test validating a password"""
        assert user.validate_password("JohnDoe1234") is True
        assert user.validate_password("JohnDoe123") is False


class TestJwtTokenMixin:
    """Test JwtTokenMixin"""

    def test_revoke_all_jwt_tokens(self, user: "User"):
        """Test revoking all jwt tokens"""
        # Create some JWT tokens for the user
        token1 = JwtToken.create(user_id=user.id, commit=False)
        token2 = JwtToken.create(user_id=user.id, commit=False)
        token3 = JwtToken.create(user_id=user.id, commit=False)
        user.jwt_tokens.extend([token1, token2, token3])  # type: ignore
        db.session.commit()

        # Revoke all JWT tokens
        user.revoke_all_jwt_tokens()

        # Check that all JWT tokens are revoked
        for token in user.get_all_jwt_tokens():
            assert token.revoked is True, "Token is not revoked"

    def test_revoke_expired_jwt_tokens(self, user: "User"):
        """Test revoking expired jwt tokens"""
        # Create some JWT tokens for the user
        token1 = JwtToken.create(user_id=user.id, commit=False)
        with update_config(
            app.config, JWT_ACCESS_TOKEN_EXPIRES=timedelta(seconds=0.5)
        ):
            token2 = JwtToken.create(user_id=user.id, commit=False)
            token3 = JwtToken.create(user_id=user.id, commit=False)

        user.jwt_tokens.extend([token1, token2, token3])  # type: ignore
        db.session.commit()

        # Wait for the JWT token to expire
        sleep(0.5)

        # Revoke expired JWT tokens
        user.revoke_expired_jwt_tokens()

        # Check that only the expired JWT token is revoked
        assert token1.revoked is False, "Token revoked"
        assert token2.revoked is True, "Token not revoked"
        assert token3.revoked is True, "Token not revoked"

    def test_revoke_jwt_token(self, user: "User"):
        """Test revoking jwt token"""
        # Create a JWT token for the user
        token = JwtToken.create(user_id=user.id, commit=False)
        user.jwt_tokens.append(token)  # type: ignore
        db.session.commit()

        # Revoke the JWT token
        user.revoke_jwt_token(token)

        # Check that the JWT token is revoked
        assert token.revoked is True

    def test_deactivate_jwt_token(self, user: "User"):
        """Test deactivating jwt token"""
        # Create a JWT token for the user
        token = JwtToken.create(user_id=user.id, commit=False)
        user.jwt_tokens.append(token)  # type: ignore
        db.session.commit()

        # Deactivate the JWT token
        user.deactivate_jwt_token(token)

        # Check that the JWT token is deactivated
        assert token.active is False

    def test_create_jwt_token(self, user: "User"):
        """Test creating jwt token"""
        # Create a JWT token for the user
        token = user.create_jwt_token()

        # Check that the JWT token is created
        assert token.id is not None
        assert token.user_id == user.id
        assert token.access_token is not None
        assert token.revoked is False
        assert token.active is True

    def test_get_jwt_token(self, user: "User"):
        """Test getting jwt token"""
        # Create a JWT token for the user
        token = JwtToken.create(user_id=user.id, commit=False)
        user.jwt_tokens.append(token)  # type: ignore
        db.session.commit()

        # Get the JWT token
        retrieved_token = user.get_jwt_token(token.access_token)

        # Check that the retrieved JWT token is correct
        assert retrieved_token is not None
        assert retrieved_token.id == token.id
        assert retrieved_token.user_id == user.id
        assert retrieved_token.access_token == token.access_token
        assert retrieved_token.revoked == token.revoked
        assert retrieved_token.active == token.active

    def test_get_all_jwt_tokens(self, user: "User"):
        """Test getting all jwt tokens"""
        # Create some JWT tokens for the user
        token1 = JwtToken.create(user_id=user.id, commit=False)
        token2 = JwtToken.create(user_id=user.id, commit=False)
        token3 = JwtToken.create(user_id=user.id, commit=False)
        user.jwt_tokens.extend([token1, token2, token3])  # type: ignore
        db.session.commit()

        # Get all JWT tokens
        tokens = user.get_all_jwt_tokens()

        # Check that all JWT tokens are retrieved
        assert len(tokens) == 3
        assert token1 in tokens
        assert token2 in tokens
        assert token3 in tokens

    def test_get_active_jwt_tokens(self, user: "User"):
        """Test getting active jwt tokens"""
        # Create some JWT tokens for the user
        token1 = JwtToken.create(user_id=user.id, commit=False)

        # Expire one of the JWT tokens
        with update_config(
            app.config, JWT_ACCESS_TOKEN_EXPIRES=timedelta(seconds=0.5)
        ):
            token2 = JwtToken.create(user_id=user.id, commit=False)

        token3 = JwtToken.create(user_id=user.id, commit=False)

        user.jwt_tokens.extend([token1, token2, token3])  # type: ignore
        db.session.commit()

        # Deactivate one of the JWT tokens
        user.deactivate_jwt_token(token3)

        # Wait for token to expire
        sleep(0.5)

        # Get active JWT tokens
        tokens = list(user.get_active_jwt_tokens())

        # Check that only the active JWT tokens are retrieved
        assert len(tokens) == 1
        assert token1 in tokens, "Active token must be enlisted"
        assert token2 not in tokens, (
            "Expired token cannot be listed as "
            "active except with_expired is True"
        )
        assert token3 not in tokens, "Deactivated token cannot be active"

    def test_get_inactive_jwt_tokens(self, user: "User"):
        """Test getting inactive jwt tokens"""
        # Create some JWT tokens for the user
        token1 = JwtToken.create(user_id=user.id, commit=False)

        # Expire one of the JWT tokens
        with update_config(
            app.config, JWT_ACCESS_TOKEN_EXPIRES=timedelta(seconds=0.5)
        ):
            token2 = JwtToken.create(user_id=user.id, commit=False)

        token3 = JwtToken.create(user_id=user.id, commit=False)

        user.jwt_tokens.extend([token1, token2, token3])  # type: ignore
        db.session.commit()

        # Deactivate one of the JWT tokens
        user.deactivate_jwt_token(token3)

        # Wait for token to expire
        sleep(0.5)

        # Get active JWT tokens
        tokens = list(user.get_inactive_jwt_tokens())

        # Check that only the active JWT tokens are retrieved
        assert len(tokens) == 1
        assert token1 not in tokens, "Active token cannot be inactive"
        assert token2 not in tokens, (
            "Expired token cannot be listed as "
            "inactive except with_expired is True"
        )
        assert token3 in tokens, "Inactivate token must be enlisted"

    def test_request_jwt_token(self, user: "User", app):
        """Test requesting a jwt token"""
        # Create JWT tokens
        token1 = user.create_jwt_token()
        token2 = user.create_jwt_token()

        # request for a token
        token = user.request_jwt_token()

        # check that an existing token was returned
        assert token.id == token2.id
        assert token.user_id == user.id
        assert token.access_token == token2.access_token
        assert token.revoked is False
        assert token.active is True

        # Create a new token with a shorter expiry time
        with update_config(
            app.config, JWT_ACCESS_TOKEN_EXPIRES=timedelta(seconds=0.5)
        ):
            token3 = user.create_jwt_token()

        # wait for token to expire
        sleep(0.5)

        # request for another token
        token = user.request_jwt_token()

        # check that an existing token was returned
        assert token.id == token2.id
        assert token.user_id == user.id
        assert token.access_token == token2.access_token
        assert token.revoked is False
        assert token.active is True

        # deactivate a token
        user.deactivate_jwt_token(token1)

        # revoke a token
        user.revoke_jwt_token(token2)

        # request for a new token
        token = user.request_jwt_token()

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
