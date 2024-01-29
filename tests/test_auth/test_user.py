"""Test user model."""

import pytest

from cookgpt.auth.models import User
from tests.utils import Random


class TestUserModel:
    """Test user model."""

    def test_create_user(self, user: "User"):
        """Test creating a user."""
        assert user.id is not None
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.email == "johndoe@example.com"
        assert user.username == "johndoe"
        assert user.password != "JohnDoe1234", "Password should be hashed"

    def test_to_dict(self, user: "User"):
        """Test to_dict method."""
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

    def test_create_user_no_last_name(self):
        """Test creating a user without a last name."""
        user = Random.user(last_name=None)
        assert user.last_name is None

    @pytest.mark.usefixtures("app")
    def test_create_user_with_same_username(self):
        """Test creating a user with the same username."""
        user = Random.user()
        with pytest.raises(User.CreateError) as excinfo:
            Random.user(username=user.username)
        excinfo.match("username is taken")

    @pytest.mark.usefixtures("app")
    def test_create_user_with_same_email(self):
        """Test creating a user with the same email."""
        user = Random.user()
        with pytest.raises(User.CreateError) as excinfo:
            Random.user(email=user.email)
        excinfo.match("email is taken")

    def test_update_user(self, user: "User"):
        """Test updating a user."""
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
        """Test updating a user with the same username."""
        user = Random.user()
        user2 = Random.user()
        with pytest.raises(User.UpdateError) as excinfo:
            user2.update(username=user.username)
        excinfo.match("username is taken")
        user.update(username=user.username)
        assert True, "Should not raise error"

    @pytest.mark.usefixtures("app")
    def test_update_user_with_same_email(self):
        """Test updating a user with the same email."""
        user = Random.user()
        user2 = Random.user()
        with pytest.raises(User.UpdateError) as excinfo:
            user2.update(email=user.email)
        excinfo.match("email is taken")
        user.update(email=user.email)
        assert True, "Should not raise error"

    def test_validate_password(self, user: "User"):
        """Test validating a password."""
        assert user.validate_password("JohnDoe1234") is True
        assert user.validate_password("JohnDoe123") is False
