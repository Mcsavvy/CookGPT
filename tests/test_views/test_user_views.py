from typing import Any, cast

import pytest
from faker import Faker
from flask import url_for
from flask.testing import FlaskClient

from cookgpt.auth.models import User
from tests.utils import Random


def get_headers(user: User):
    return {"Authorization": f"Bearer {user.request_token().access_token}"}


@pytest.mark.usefixtures("app")
class TestUserView:
    def test_get_user(self, client: FlaskClient, random_user: User):
        headers = get_headers(random_user)
        response = client.get(url_for("auth.user"), headers=headers)
        assert response.status_code == 200

        data = cast(dict[str, Any], response.json)

        assert data["id"] == random_user.uid
        assert data["email"] == random_user.email
        assert data["first_name"] == random_user.first_name
        assert data["last_name"] == random_user.last_name
        assert data["username"] == random_user.username
        assert data["user_type"] == random_user.type.name
        assert data["profile_picture"] == random_user.profile_picture
        assert data["max_chat_cost"] == random_user.max_chat_cost
        assert data["total_chat_cost"] == random_user.total_chat_cost

    def test_patch_user(
        self, client: FlaskClient, random_user: User, faker: Faker
    ):
        headers = get_headers(random_user)
        new_email = faker.email()
        old_profile_picture = random_user.profile_picture
        old_password = faker.password()
        new_password = faker.password()

        first_name = random_user.first_name
        last_name = random_user.last_name
        username = random_user.username
        random_user.update(password=old_password)

        assert random_user.validate_password(
            old_password
        ), "Password should be valid"
        update_data = {
            "email": new_email,
            "password": new_password,
        }

        response = client.patch(
            url_for("auth.user"), json=update_data, headers=headers
        )
        assert response.status_code == 200

        assert (
            random_user.validate_password(old_password) is False
        ), "Password should be invalid"
        assert (
            random_user.validate_password(new_password) is True
        ), "Password should be valid"
        assert random_user.email == new_email
        assert (
            random_user.profile_picture != old_profile_picture
        ), "Profile picture should be updated"

        assert random_user.first_name == first_name
        assert random_user.last_name == last_name
        assert random_user.username == username

    def test_update_user__existing_email(
        self, client: FlaskClient, random_user: User, faker: Faker
    ):
        # when email is already taken by another user
        email = Random.user().email
        headers = get_headers(random_user)

        update_data = {
            "email": email,
        }
        response = client.patch(
            url_for("auth.user"), json=update_data, headers=headers
        )
        assert response.status_code == 422

        # when email is already taken by the same user
        update_data = {
            "email": random_user.email,
        }
        response = client.patch(
            url_for("auth.user"), json=update_data, headers=headers
        )
        assert response.status_code == 200

    def test_update_user__existing_username(
        self, client: FlaskClient, random_user: User, faker: Faker
    ):
        # when username is already taken by another user
        username = Random.user().username
        headers = get_headers(random_user)

        update_data = {
            "username": username,
        }
        response = client.patch(
            url_for("auth.user"), json=update_data, headers=headers
        )
        assert response.status_code == 422

        # when username is already taken by the same user
        update_data = {
            "username": random_user.username,
        }
        response = client.patch(
            url_for("auth.user"), json=update_data, headers=headers
        )
        assert response.status_code == 200

    def test_delete_user(self, client: FlaskClient, random_user: User):
        headers = get_headers(random_user)
        response = client.delete(url_for("auth.user"), headers=headers)
        assert response.status_code == 422
        assert User.query.get(random_user.id), "User should not be deleted"
