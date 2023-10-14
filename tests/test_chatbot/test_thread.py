from typing import cast
from uuid import uuid4

import pytest

from cookgpt.auth.models import User
from cookgpt.chatbot.models import Chat, MessageType, Thread
from tests.utils import Random


class TestThreadModel:
    def test_create_thread(self, user):
        user_id = user.id
        thread = Thread.create(
            title="Test Thread",
            user_id=user_id,
            closed=False,
            default=False,
            commit=True,
        )

        assert thread.id is not None
        assert thread.title == "Test Thread"
        assert thread.user_id == user_id
        assert thread.closed is False
        assert thread.default is False

    def test_add_chat(self, thread: Thread):
        thread2 = Random.user().default_thread
        chat = thread.add_chat(
            content="What's your name?",
            chat_type=MessageType.QUERY,
            cost=10,
            commit=True,
        )
        assert chat.chat_type == MessageType.QUERY
        assert chat in cast(list[Chat], thread.chats)
        assert chat.thread_id == thread.id
        assert chat.order == 0
        assert chat.previous_chat is None
        assert chat.next_chat is None
        assert chat.content == "What's your name?"
        assert chat.cost == 10

        # adding messages across different threads
        with pytest.raises(ValueError) as exc_info:
            thread2.add_chat(
                content="My name is Bot.",
                chat_type=MessageType.RESPONSE,
                cost=10,
                previous_chat=chat,
                commit=True,
            )
        exc_info.match("previous_chat not in same thread")

    def test_add_query(self, thread: Thread):
        chat = thread.add_query(
            content="What's your name?",
            cost=5,
            commit=True,
        )
        assert chat.chat_type == MessageType.QUERY
        assert chat in cast(list[Chat], thread.chats)
        assert chat.thread_id == thread.id
        assert chat.order == 0
        assert chat.previous_chat is None
        assert chat.next_chat is None
        assert chat.content == "What's your name?"
        assert chat.cost == 5

    def test_add_response(self, thread: Thread):
        query = thread.add_query(
            content="What's your name?",
            cost=5,
            commit=True,
        )

        response = thread.add_response(
            content="My name is Bot.",
            cost=0,
            previous_chat=query,
            commit=True,
        )

        assert response.content == "My name is Bot."
        assert response.chat_type == MessageType.RESPONSE
        assert response.cost == 0
        assert response.thread_id == thread.id
        assert response.previous_chat_id == query.id
        assert response.order == 1

    def test_close_thread(self, thread: Thread):
        thread.close()
        assert thread.closed is True

    def test_chat_threading(self, thread: Thread, faker):
        for i in range(10):
            thread.add_query(
                content=faker.sentence(),
                cost=5,
                commit=True,
            )

        chats = cast(list[Chat], thread.chats)

        assert len(chats) == 10  # type: ignore

        for i in range(10):
            assert chats[i].order == i  # type: ignore

        for i in range(10):
            assert chats[i].previous_chat == (chats[i - 1] if i > 0 else None)
            assert chats[i].next_chat == (chats[i + 1] if i < 9 else None)

    def test_clear_thread(self, thread: Thread, faker):
        for i in range(10):
            thread.add_query(
                content=faker.sentence(),
                cost=5,
                commit=True,
            )

        thread.clear()
        assert len(thread.chats) == 0  # type: ignore


class TestThreadMixin:
    def test_create_thread(self, user: "User"):
        thread = user.create_thread(
            title="Test Thread",
            closed=False,
            default=False,
        )

        assert thread.id is not None
        assert thread.title == "Test Thread"
        assert thread.user_id == user.id
        assert thread.closed is False
        assert thread.default is False

    def test_get_threads(self, user: "User"):
        thread1 = user.create_thread(
            title="Test Thread 1",
            closed=False,
            default=False,
        )
        thread2 = user.create_thread(
            title="Test Thread 2",
            closed=False,
            default=False,
        )

        threads = cast(list[Thread], user.threads)

        assert len(threads) == 2
        assert thread1 in threads
        assert thread2 in threads

    def test_add_query_message(self, user: "User"):
        thread = user.create_thread(title="Test Thread", closed=False)
        query = user.add_message(
            content="What's your name?",
            chat_type=MessageType.QUERY,
            cost=10,
            commit=True,
            thread_id=thread.id,
        )

        assert query.chat_type == MessageType.QUERY
        assert query in cast(list[Chat], thread.chats)
        assert query.thread_id == thread.id
        assert query.order == 0
        assert query.previous_chat is None
        assert query.next_chat is None
        assert query.content == "What's your name?"
        assert query.cost == 10

    def test_add_response_message_using_previous_chat(self, user: "User"):
        thread = user.create_thread(title="Test Thread", closed=False)
        query = user.add_message(
            content="What's your name?",
            chat_type=MessageType.QUERY,
            cost=10,
            commit=True,
            thread_id=thread.id,
        )
        response = user.add_message(
            content="My name is Bot.",
            chat_type=MessageType.RESPONSE,
            cost=10,
            previous_chat=query,
            commit=True,
        )
        assert response.chat_type == MessageType.RESPONSE
        assert response in cast(list[Chat], thread.chats)
        assert response.thread_id == thread.id
        assert response.order == 1
        assert response.previous_chat == query
        assert response.next_chat is None
        assert response.content == "My name is Bot."
        assert response.cost == 10
        assert query.next_chat == response
        assert response.previous_chat_id == query.id

    def test_add_query_message_using_thread_id(self, user: "User"):
        thread = user.create_thread(title="Test Thread", closed=False)
        query = user.add_message(
            content="What's your name?",
            chat_type=MessageType.QUERY,
            cost=10,
            thread_id=thread.id,
            commit=True,
        )

        assert query.chat_type == MessageType.QUERY
        assert query in cast(list[Chat], thread.chats)
        assert query.thread_id == thread.id
        assert query.order == 0

    def test_add_message_to_non_existent_thread(self, user: "User"):
        with pytest.raises(ValueError) as exc_info:
            user.add_message(
                content="My name is Bot.",
                chat_type=MessageType.RESPONSE,
                cost=10,
                thread_id=uuid4(),
                commit=True,
            )
        exc_info.match("thread_id is invalid")

    def test_add_message_to_another_users_thread(self, user: "User"):
        user2 = Random.user()
        thread2 = user2.create_thread(
            title="Test Thread 2", closed=False, default=False
        )
        with pytest.raises(ValueError) as exc_info:
            user.add_message(
                content="My name is Bot.",
                chat_type=MessageType.RESPONSE,
                cost=10,
                thread_id=thread2.id,
                commit=True,
            )
        exc_info.match("thread not owned by user")

    def test_add_message__no_thread_id_or_previous_chat(self, user: "User"):
        """test add_message method with no thread_id or previous_chat"""
        with pytest.raises(RuntimeError) as exc_info:
            user.add_message(
                content="My name is Bot.",
                chat_type=MessageType.RESPONSE,
                cost=10,
                commit=True,
            )
        exc_info.match("thread_id or previous_chat must be given")

    def test_add_query(self, user: "User"):
        """test add_query method"""
        thread = user.create_thread(title="Test Thread", closed=False)
        query = user.add_query(
            content="What's your name?",
            cost=5,
            commit=True,
            thread_id=thread.id,
        )
        assert query.chat_type == MessageType.QUERY
        assert query in cast(list[Chat], thread.chats)
        assert query.thread_id == thread.id
        assert query.order == 0
        assert query.previous_chat is None
        assert query.next_chat is None
        assert query.content == "What's your name?"
        assert query.cost == 5

    def test_add_response(self, user: "User"):
        """test add_response method"""
        thread = user.create_thread(
            title="Test Thread",
            closed=False,
        )
        query = user.add_query(
            content="What's your name?",
            cost=5,
            commit=True,
            thread_id=thread.id,
        )
        response = user.add_response(
            content="My name is Bot.",
            cost=5,
            previous_chat=query,
            commit=True,
            thread_id=thread.id,
        )
        assert response.chat_type == MessageType.RESPONSE
        assert response in cast(list[Chat], thread.chats)
        assert response.thread_id == thread.id
        assert response.order == 1
        assert response.previous_chat == query
        assert response.next_chat is None
        assert response.content == "My name is Bot."
        assert response.cost == 5
        assert query.next_chat == response
        assert response.previous_chat_id == query.id

    def test_total_chat_cost(self, user: "User"):
        """test total_chat_cost property"""
        for t in range(5):
            thread = user.create_thread(
                title=f"Test Thread {t}",
                closed=False,
            )
            for c in range(5):
                Random.chat(thread_id=thread.id, order=c, cost=5)

        assert user.total_chat_cost == 125

    def test_clear_chats(self, user: "User"):
        """test clear_chats method"""

        for t in range(5):
            thread = user.create_thread(
                title=f"Test Thread {t}",
                closed=False,
            )
            for c in range(5):
                user.add_response(
                    content=f"Response {c}",
                    cost=5,
                    previous_chat=user.add_query(
                        content=f"Query {c}",
                        cost=5,
                        commit=True,
                        thread_id=thread.id,
                    ),
                    commit=True,
                )

        threads = cast(list[Thread], user.threads)
        user.clear_chats(threads)
        assert len(threads) == 5
        for thread in threads:
            assert len(thread.chats) == 0  # type: ignore
