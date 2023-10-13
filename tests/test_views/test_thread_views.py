from uuid import uuid4

import pytest
from flask import url_for
from flask.testing import FlaskClient

from cookgpt.auth.models.user import User
from cookgpt.chatbot.models import Chat, Thread
from cookgpt.chatbot.utils import get_thread
from tests.utils import Random


@pytest.mark.usefixtures("user")
class TestThreadView:
    def test_get_thread(
        self, client: FlaskClient, user: "User", auth_header: dict[str, str]
    ):
        thread = user.create_thread(title="Test Thread")
        for i in range(2):
            Random.chat(thread_id=thread.id, order=i)
        response = client.get(
            url_for("chatbot.single_thread", thread_id=thread.id),
            headers=auth_header,
        )
        assert response.status_code == 200

        data = response.json
        assert data["id"] == str(thread.id)
        assert data["title"] == "Test Thread"
        assert data["chat_count"] == 2
        assert data["cost"] != 0
        assert data["is_default"] is False
        thread.delete()

    def test_get_thread_not_found(
        self, client: FlaskClient, auth_header: dict
    ):
        response = client.get(
            url_for("chatbot.single_thread", thread_id=uuid4()),
            headers=auth_header,
        )
        assert response.status_code == 404

    def test_get_default_thread(
        self, client: FlaskClient, thread: Thread, auth_header: dict
    ):
        response = client.get(
            url_for("chatbot.single_thread", thread_id=thread.id),
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json
        assert data["id"] == str(thread.id)
        assert data["title"] == "Test Thread"
        assert data["chat_count"] == 0
        assert data["cost"] == 0
        assert data["is_default"] is True

    def test_create_thread(self, client: FlaskClient, auth_header: dict):
        response = client.post(
            url_for("chatbot.create_thread"),
            json={"title": "New Thread"},
            headers=auth_header,
        )
        assert response.status_code == 201

        assert response.json.get("message")

        data = response.json["thread"]
        assert data["id"]
        assert data["title"] == "New Thread"
        assert data["chat_count"] == 0
        assert data["cost"] == 0
        assert data["is_default"] is False
        thread = get_thread(data["id"])
        thread.delete()

    def test_update_thread(
        self, client: FlaskClient, user: "User", auth_header: dict
    ):
        thread = user.create_thread(title="Test Thread")
        response = client.patch(
            url_for("chatbot.single_thread", thread_id=thread.id),
            json={"title": "Updated Thread"},
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.json.get("message")

        data = response.json["thread"]
        assert data["id"] == str(thread.id)
        assert data["title"] == "Updated Thread"
        assert data["chat_count"] == 0
        assert data["cost"] == 0
        assert data["is_default"] is False
        thread.delete()

    def test_delete_thread(
        self, client: FlaskClient, user: "User", auth_header: dict
    ):
        thread = user.create_thread(title="Test Thread")
        for i in range(3):
            Random.chat(thread_id=thread.id, order=i)
        response = client.delete(
            url_for("chatbot.single_thread", thread_id=thread.id),
            headers=auth_header,
        )
        assert response.status_code == 200
        assert get_thread(thread.id, required=False) is None
        assert len(Chat.query.filter(Chat.thread_id == thread.id).all()) == 0


@pytest.mark.usefixtures("user")
class TestThreadsView:
    def test_get_threads(
        self, client: FlaskClient, user: User, auth_header: dict
    ):
        """Test getting all threads"""
        # delete all threads
        response = client.get(
            url_for("chatbot.all_threads"), headers=auth_header
        )
        assert response.status_code == 200
        assert len(response.json["threads"]) == 0

        user.create_thread(title="Test Thread 1")
        user.create_thread(title="Test Thread 2")
        response = client.get(
            url_for("chatbot.all_threads"), headers=auth_header
        )
        assert response.status_code == 200
        assert len(response.json["threads"]) == 2
        for thread in response.json["threads"]:
            assert thread["id"]
            assert thread["title"]
            assert thread["chat_count"] == 0
            assert thread["cost"] == 0
            assert thread["is_default"] is False

    def test_delete_threads(
        self, client: FlaskClient, user: User, auth_header: dict
    ):
        """Test deleting all threads"""

        user.create_thread(title="Test Thread 1")
        user.create_thread(title="Test Thread 2")
        response = client.delete(
            url_for("chatbot.all_threads"), headers=auth_header
        )
        assert response.status_code == 200
        assert len(Thread.query.all()) == 0
