"""Tests for Chat model."""

import pytest
from sqlalchemy.exc import IntegrityError

from cookgpt.chatbot.models import Chat, MessageType, Thread
from cookgpt.ext import db


class TestChatModel:
    """Test Chat model."""

    def test_create_chat(self, thread: "Thread"):
        """Test creating a chat."""
        chat = Chat.create(
            content="Hello, World!",
            cost=10,
            chat_type=MessageType.RESPONSE,
            thread_id=thread.id,
            order=1,
        )

        assert chat.id is not None
        assert chat.content == "Hello, World!"
        assert chat.cost == 10
        assert chat.chat_type == MessageType.RESPONSE
        assert chat.thread_id == thread.id
        assert chat.sent_time is not None
        assert chat.order == 1

    def test_get_next_chat_id(self, thread: "Thread"):
        """Test getting next chat id."""
        chat1 = Chat.create(
            content="Hello, World!",
            cost=10,
            chat_type=MessageType.RESPONSE,
            thread_id=thread.id,
            order=1,
        )
        chat2 = Chat.create(
            content="How are you?",
            cost=5,
            chat_type=MessageType.QUERY,
            thread_id=thread.id,
            order=2,
        )
        chat1.update(next_chat=chat2)
        assert chat1.next_chat_id == chat2.id
        assert chat2.next_chat_id is None

    def test_unique_order_per_thread(self, thread: "Thread"):
        """Test unique order per thread."""
        Chat.create(
            content="Hello, World!",
            cost=10,
            chat_type=MessageType.RESPONSE,
            thread_id=thread.id,
            order=1,
        )
        with pytest.raises(IntegrityError):
            Chat.create(
                content="How are you?",
                cost=5,
                chat_type=MessageType.RESPONSE,
                thread_id=thread.id,
                order=1,
            )
        db.session.rollback()

    def test_delete_chat(self, thread: "Thread"):
        """Test deleting a chat."""
        chat = Chat.create(
            content="Hello, World!",
            cost=10,
            chat_type=MessageType.RESPONSE,
            thread_id=thread.id,
            order=1,
        )

        chat_id = chat.id
        chat.delete()

        assert db.session.get(Chat, chat_id) is None
