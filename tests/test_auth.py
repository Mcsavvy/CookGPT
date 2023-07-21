"""Test authentication"""
from typing import cast
from uuid import UUID

from flask import request, url_for
from flask.testing import FlaskClient as Client
from flask_jwt_extended import decode_token

from cookgpt.auth.models import JwtToken
from cookgpt.user.models import User
from tests import (
    extract_access_token,
    random_email,
    random_first_name,
    random_last_name,
    random_password,
    random_username,
)


class TestJwtTokenModel:
    """Test JWT token model"""

    def test_create(self, user: "User"):
        """Test create"""
        token = JwtToken.create(user_id=user.id)
        assert token.id is not None
        assert token.user_id == user.id
        assert token.access_token is not None
        assert token.revoked is False
        assert token.active is True
        assert token.is_expired is False

    def test_access_token_created_before_model_is_committed(
        self, user: "User"
    ):
        """Test access token is created before model is committed"""
        token = JwtToken.create(user_id=user.id, commit=False)
        assert token.access_token is not None

    def test_jwt_token_id_matches_jti(self, user: "User"):
        """Test that JtwToken.id matches the identity in the access_token"""
        token = JwtToken.create(user_id=user.id, commit=True)
        payload = decode_token(token.access_token)
        assert token.id == UUID(payload["jti"])

    def test_convert_jti_to_jwt_token(self, user: "User"):
        """Test jti conversion to token"""
        token = JwtToken.create(user_id=user.id, commit=True)
        payload = decode_token(token.access_token)
        token_ = JwtToken.query.get(UUID(payload["jti"]))

        assert token_ == token

    def test_to_dict(self, user: "User"):
        """Test to_dict method"""
        keys = [
            "id",
            "user_id",
            "access_token",
            "revoked",
            "active",
            "created_at",
            "updated_at",
        ]
        token = JwtToken.create(user_id=user.id, commit=False)
        dict = token.to_dict()
        for key in keys:
            assert key in dict, f"{key} not in dict"


class TestLoginView:
    def test_login_valid_email(self, client: "Client", user: "User"):
        """Test login with valid email"""
        data = {"login": user.email, "password": "JohnDoe1234"}
        response = client.post(url_for("auth.login"), json=data)
        json = cast(dict, response.json)
        print(json)
        assert response.status_code == 200
        assert json["message"] == "Successfully logged in"
        assert "x_access_token" in response.headers["Set-Cookie"]

    def test_login_valid_username(self, client, user: "User"):
        """Test login with valid username"""
        data = {"login": user.username, "password": "JohnDoe1234"}
        response = client.post(url_for("auth.login"), json=data)
        json = cast(dict, response.json)
        assert response.status_code == 200
        assert json["message"] == "Successfully logged in"
        assert "x_access_token" in response.headers["Set-Cookie"]

    def test_access_token_valid(self, client: "Client", user: "User"):
        """Test that the access token returned is valid"""
        data = {"login": user.email, "password": "JohnDoe1234"}
        response = client.post(url_for("auth.login"), json=data)
        access_token = extract_access_token(response)

        token = JwtToken.query.filter_by(access_token=access_token).first()
        assert token is not None
        assert token.user_id == user.id
        assert token.revoked is False
        assert token.active is True
        assert token.is_expired is False

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
        token = user.request_jwt_token()
        client.set_cookie("localhost", "x_access_token", token.access_token)
        response = client.post(url_for("auth.logout"))
        json = cast(dict, response.json)

        print(request.headers)
        print(response.headers)
        assert response.status_code == 200
        assert json["message"] == "Successfully logged out"

    def test_access_cookie_unset(self, client: "Client", user: "User"):
        """Test access_token cookie unset"""

        token = user.request_jwt_token()
        client.set_cookie("localhost", "x_access_token", token.access_token)
        response = client.post(url_for("auth.logout"))

        access_token = (
            response.headers["Set-Cookie"].split(";")[0].split("=")[1]
        )

        assert access_token == ""


class TestSignupView:
    """Test signup logic"""

    def random_user_data(self, **kwargs):
        """generate random user data"""
        kwargs.setdefault("first_name", random_first_name())
        kwargs.setdefault("last_name", random_last_name())
        kwargs.setdefault("email", random_email())
        kwargs.setdefault("username", random_username())
        kwargs.setdefault("password", random_password())
        return kwargs

    def test_signup_valid_data(self, client: "Client"):
        """Test signup with valid data"""
        data = self.random_user_data()
        response = client.post(url_for("auth.signup"), json=data)
        assert response.status_code == 201
        assert response.json == {"message": "Successfully signed up"}

    def test_signup_missing_data(self, client: "Client"):
        """Test signup with missing data"""
        data = self.random_user_data()
        data.pop("email")
        response = client.post(url_for("auth.signup"), json=data)
        assert response.status_code == 422

    def test_signup_invalid_data(self, client: "Client"):
        """Test signup with invalid data"""
        data = self.random_user_data()
        data["password"] = "password"
        response = client.post(url_for("auth.signup"), json=data)
        assert response.status_code == 422

    def test_signup_existing_user(self, client: "Client", user: "User"):
        """Test signup with existing user"""
        data = self.random_user_data()
        data["email"] = user.email
        response = client.post(url_for("auth.signup"), json=data)
        assert response.status_code == 422
        assert response.json == {"message": "email is taken"}

        data = self.random_user_data()
        data["username"] = user.username
        response = client.post(url_for("auth.signup"), json=data)
        assert response.status_code == 422
        assert response.json == {"message": "username is taken"}


"""
more unittests at the beginning

- unittests
- integration test
- end-to-end tests

* vite/vitest
* jest
* @test-library/react
* @test-library/user
* Kent C. Dodds

State Machine
=============
Design a system that depicts how data flows through your system
"""
