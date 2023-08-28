from typing import cast
from uuid import uuid4

from flask import url_for
from flask.testing import FlaskClient

from cookgpt.chatbot.data.enums import MessageType
from cookgpt.chatbot.models import Chat, Thread
from tests.utils import Random


class TestThreadView:
    """Test the thread view"""

    def test_get_all_chats_in_thread(
        self, client: "FlaskClient", access_token, query: "Chat"
    ):
        """Test that a user can get all the chats in a thread"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get(url_for("chatbot.thread"), headers=headers)

        assert response.status_code == 200
        assert response.json is not None
        assert "chats" in response.json
        assert len(response.json["chats"]) == 1

        chat = response.json["chats"][0]
        assert chat["id"] == str(query.id)
        assert chat["content"] == query.content
        assert chat["chat_type"] == "QUERY"
        assert chat["thread_id"] == str(query.thread_id)
        assert chat["cost"] == query.cost
        assert chat["previous_chat_id"] is None
        assert chat["next_chat_id"] is None

    def test_delete_all_chats_in_thread(
        self, client, access_token, thread: "Thread"
    ):
        """Test that a user can delete all chats in a thread"""
        for i in range(2):
            Random.chat(thread_id=thread.id, order=i)

        assert len(cast(list[Chat], thread.chats)) == 2
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.delete(url_for("chatbot.thread"), headers=headers)

        assert response.status_code == 200
        assert "message" in response.json
        assert "deleted" in response.json["message"].lower()
        assert len(cast(list[Chat], thread.chats)) == 0


class TestChatView:
    """Test the chat view"""

    def test_get_chat(
        self, client: "FlaskClient", access_token, query: "Chat"
    ):
        """test get a chat"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get(
            url_for("chatbot.chat", chat_id=query.id), headers=headers
        )

        assert response.status_code == 200
        assert response.json is not None
        chat = response.json

        assert chat["id"] == str(query.id)
        assert chat["content"] == query.content
        assert chat["chat_type"] == "QUERY"
        assert chat["thread_id"] == str(query.thread_id)
        assert chat["cost"] == query.cost
        assert chat["previous_chat_id"] is None
        assert chat["next_chat_id"] is None

    def test_get_non_existent_chat(self, client: "FlaskClient", access_token):
        """test get a chat that does not exist"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get(
            url_for("chatbot.chat", chat_id=uuid4()), headers=headers
        )

        assert response.status_code == 404
        assert response.json is not None
        assert "message" in response.json
        assert "not found" in response.json["message"].lower()

    def test_delete_chat(
        self,
        client: "FlaskClient",
        access_token: str,
        thread: "Thread",
    ):
        """test delete a chat"""
        query = Random.chat(thread_id=thread.id, order=0)
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.delete(
            url_for("chatbot.chat", chat_id=query.id), headers=headers
        )

        assert response.status_code == 200
        assert response.json is not None
        assert "message" in response.json
        assert "deleted" in response.json["message"].lower()

    def test_delete_non_existent_chat(
        self, client: "FlaskClient", access_token
    ):
        """test delete a chat that does not exist"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.delete(
            url_for("chatbot.chat", chat_id=uuid4()), headers=headers
        )

        assert response.status_code == 404
        assert response.json is not None
        assert "message" in response.json
        assert "not found" in response.json["message"].lower()

    def test_send_query(
        self, client: "FlaskClient", access_token, thread: "Thread"
    ):
        """Send a query to the chatbot"""
        headers = {"Authorization": f"Bearer {access_token}"}
        data = {"query": "test query"}
        response = client.post(
            url_for("chatbot.query"), headers=headers, json=data
        )

        assert response.status_code == 201
        assert response.json is not None

        chats = cast(list[Chat], thread.chats)

        assert len(chats) == 2
        assert chats[0].content == "test query"
        assert chats[0].chat_type == MessageType.QUERY
        assert chats[0].thread_id == thread.id
        # assert chats[0].cost == 0
        assert chats[0].previous_chat_id is None
        assert chats[0].next_chat_id == chats[1].id
        assert chats[1].previous_chat_id == chats[0].id
        assert chats[1].next_chat_id is None
        assert chats[1].thread_id == thread.id
        assert chats[1].chat_type == MessageType.RESPONSE

    def test_send_query_exceeded_max_chat_cost(
        self, client: "FlaskClient", access_token, thread: "Thread"
    ):
        """
        Test that a user gets dummy response when they
        exceed max chat cost
        """
        thread.user.update(max_chat_cost=0)
        headers = {"Authorization": f"Bearer {access_token}"}
        data = {"query": "test query"}
        response = client.post(
            url_for("chatbot.query"), headers=headers, json=data
        )
        assert response.status_code == 200
        assert response.json is not None

        assert len(cast(list[Chat], thread.chats)) == 0

        assert response.json["cost"] == 0
        assert response.json["thread_id"] == str(thread.id)
        assert response.json["previous_chat_id"] is None
        assert response.json["next_chat_id"] is None
