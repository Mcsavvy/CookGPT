from datetime import timedelta
from typing import cast

import pytest
from flask import url_for
from flask.testing import FlaskClient as Client

from cookgpt.auth.models import Token, User
from cookgpt.ext.database import db
from tests.utils import Random, mock_config


class TestLoginView:
    def test_login_valid_email(self, client: "Client", user: "User"):
        """Test login with valid email"""
        data = {"login": user.email, "password": "JohnDoe1234"}
        response = client.post(url_for("auth.login"), json=data)
        json = cast(dict, response.json)
        assert response.status_code == 200
        assert json["message"] == "Successfully logged in"

        expected_keys = [
            "atoken",
            "rtoken",
            "atoken_expiry",
            "rtoken_expiry",
            "user_type",
            "auth_type",
        ]
        for key in expected_keys:
            assert key in json, f"{key} not in response body"

    def test_login_valid_username(self, client, user: "User"):
        """Test login with valid username"""
        data = {"login": user.username, "password": "JohnDoe1234"}
        response = client.post(url_for("auth.login"), json=data)
        json = cast(dict, response.json)
        assert response.status_code == 200
        assert json["message"] == "Successfully logged in"

        expected_keys = [
            "atoken",
            "rtoken",
            "atoken_expiry",
            "rtoken_expiry",
            "user_type",
            "auth_type",
        ]
        for key in expected_keys:
            assert key in json, f"{key} not in response body"

    def test_tokens_valid(self, client: "Client", user: "User"):
        """Test that the access token returned is valid"""
        data = {"login": user.email, "password": "JohnDoe1234"}
        response = client.post(url_for("auth.login"), json=data)
        json = cast(dict, response.json)
        access_token = json["atoken"]
        refresh_token = json["rtoken"]
        token = Token.query.filter_by(access_token=access_token).first()
        token2 = Token.query.filter_by(refresh_token=refresh_token).first()
        assert token is not None, "Token not found"
        assert token2 == token
        assert token.user_id == user.id
        assert token.revoked is False
        assert token.active is True

    def test_login_invalid_login(self, client: "Client"):
        """Test login with invalid login"""
        data = {"login": "invalid", "password": "JohnDoe1234"}
        response = client.post(url_for("auth.login"), json=data)
        json = cast(dict, response.json)
        assert response.status_code == 404
        assert json["message"] == "User does not exist"

    def test_login_invalid_password(self, client: "Client", user: "User"):
        """Test login with invalid password"""
        data = {"login": user.email, "password": "Password1234"}
        response = client.post(url_for("auth.login"), json=data)
        json = cast(dict, response.json)
        assert response.status_code == 401
        assert json["message"] == "Cannot authenticate"


class TestLogoutView:
    """Test logout route"""

    def test_logout(self, client: "Client", user: "User"):
        """Test logout"""
        token = user.request_token()
        headers = {"Authorization": f"Bearer {token.access_token}"}
        response = client.post(url_for("auth.logout"), headers=headers)
        json = cast(dict, response.json)
        assert response.status_code == 200
        assert json["message"] == "Logged out user"
        assert token.active is False
        assert token.revoked is False


class TestSignupView:
    """Test signup logic"""

    def test_signup_valid_data(self, client: "Client"):
        """Test signup with valid data"""
        data = Random.user_data()
        response = client.post(url_for("auth.signup"), json=data)
        assert response.status_code == 201
        assert response.json == {"message": "Successfully signed up"}

    def test_signup_missing_data(self, client: "Client"):
        """Test signup with missing data"""
        data = Random.user_data(email=False)
        response = client.post(url_for("auth.signup"), json=data)
        assert response.status_code == 406

    def test_signup_invalid_data(self, client: "Client"):
        """Test signup with invalid data"""
        data = Random.user_data(password="password")
        response = client.post(url_for("auth.signup"), json=data)
        assert response.status_code == 406

    def test_signup_existing_user(self, client: "Client", user: "User"):
        """Test signup with existing user"""
        data = Random.user_data(email=user.email)
        response = client.post(url_for("auth.signup"), json=data)
        assert response.status_code == 422
        assert response.json == {"message": "email is taken"}

        data = Random.user_data(username=user.username)
        response = client.post(url_for("auth.signup"), json=data)
        assert response.status_code == 422
        assert response.json == {"message": "username is taken"}


class TestRefreshView:
    """Test token refresh view"""

    @pytest.mark.skip  # TODO: fix sqlalchemy UPDATE issue
    def test_refresh_access_token(
        self, user: "User", client: "Client", config
    ):
        """test refresh access token"""
        with mock_config(
            config, JWT_ACCESS_TOKEN_EXPIRES=timedelta(seconds=10)
        ):
            # BUG: 2 jwt's created at the same time would be identical,
            # so I need to make sure the expiration time varies
            token = user.create_token()
        old_atoken = token.access_token
        headers = {"Authorization": f"Bearer {token.refresh_token}"}
        response = client.post(url_for("auth.refresh"), headers=headers)
        json = cast(dict, response.json)
        assert response.status_code == 200
        assert json["message"] == "Refreshed access token"
        db.session.refresh(token)

        expected_keys = [
            "atoken",
            "rtoken",
            "atoken_expiry",
            "rtoken_expiry",
            "user_type",
            "auth_type",
        ]
        for key in expected_keys:
            assert key in json, f"{key} not in response body"

        assert old_atoken != token.access_token
