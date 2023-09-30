from random import randint
from typing import TYPE_CHECKING, Generator

import pytest

from cookgpt import create_app
from cookgpt.auth.models import User
from cookgpt.chatbot.models import Chat, MessageType, Thread
from cookgpt.ext import config
from cookgpt.ext.database import db
from tests.utils import Random

if TYPE_CHECKING:  # pragma: no cover
    from cookgpt.app import App


pytest_plugins = ("celery.contrib.pytest",)


@pytest.fixture(scope="session")
def app() -> Generator["App", None, None]:
    """An instance of the Flask application"""
    old_env = config.current_env
    config.setenv("testing")
    app = create_app()
    app_ctx = app.app_context()
    app_ctx.push()
    db.create_all()
    try:
        yield app
    finally:
        db.session.rollback()
        db.drop_all()
        app_ctx.pop()
        config.setenv(old_env)


@pytest.fixture(scope="function")
def user(app: "App") -> Generator[User, None, None]:
    """An instance of a User"""
    user = User.create(
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        username="johndoe",
        password="JohnDoe1234",
        commit=True,
    )
    yield user
    user.delete()


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("app")
def random_user():
    """A random user"""
    user = Random.user()
    yield user
    user.delete()


@pytest.fixture(scope="session")
def faker_seed():
    """A seed for the faker instance"""
    return randint(1000, 99999)


@pytest.fixture(scope="session")
def faker():
    """An instance of the Faker class"""
    from faker import Faker

    return Faker()


@pytest.fixture(scope="function")
def access_token(user: User) -> str:
    """A valid access token for the user"""
    return user.create_token().access_token


@pytest.fixture(scope="function")
def thread(user: User) -> Generator[Thread, None, None]:
    """An instance of a Thread"""
    thread = Thread.create(
        user_id=user.id,
        title="Test Thread",
        default=True,
        commit=True,
    )
    yield thread
    thread.delete()


@pytest.fixture(scope="function")
def response(thread: Thread):
    """An AI response"""
    response = Chat.create(
        content="Hello, how are you doing today?",
        cost=10,
        chat_type=MessageType.RESPONSE,
        thread_id=thread.id,
        order=1,
        commit=True,
    )
    yield response
    response.delete()


@pytest.fixture(scope="function")
def query(thread: Thread):
    """A user query"""
    query = Chat.create(
        content="Hi!",
        cost=5,
        chat_type=MessageType.QUERY,
        thread_id=thread.id,
        order=0,
        commit=True,
    )
    yield query
    query.delete()


@pytest.fixture(scope="function")
def random_chat(thread: Thread):
    """A random chat"""
    chat = Random.chat(thread_id=thread.id)
    yield chat
    chat.delete()


@pytest.fixture(scope="session")
def celery_worker_parameters():
    return {
        "perform_ping_check": False,
        "loglevel": "INFO",
    }


@pytest.fixture(scope="session")
def celery_app(app: "App"):
    """An instance of the Celery application"""
    from redisflow import celeryapp

    celeryapp.init_app(app)
    return celeryapp


@pytest.fixture(scope="session")
def celery_worker_pool():
    """You can override this fixture to set the worker pool.

    The "solo" pool is used by default, but you can set this to
    return e.g. "prefork".
    """
    return "prefork"
