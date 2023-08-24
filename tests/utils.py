"""utilities for testing"""
from contextlib import contextmanager
from typing import Any

from faker import Faker

from cookgpt.chatbot.data.enums import MessageType
from cookgpt.utils import utcnow

fake = Faker()

_Missing = object()


@contextmanager
def mock_config(config, **vars):
    """update the app's config temporarily"""
    undefined = object()
    old_config = {}
    for k, v in vars.items():
        old_config[k] = config.get(k, undefined)
        config[k] = v
    try:
        yield
    finally:
        for k, v in old_config.items():
            if v is undefined:
                del config[k]
            else:
                config[k] = v


class Random:
    """a namespace for random data"""

    @classmethod
    def first_name(cls):
        """return a random first name"""
        return fake.first_name()

    @classmethod
    def last_name(cls):
        """return a random last name"""
        return fake.last_name()

    @classmethod
    def username(cls):
        """return a random username"""
        username = fake.user_name()
        while len(username) < 5:
            username = fake.user_name()
        return username

    @classmethod
    def email(cls):
        """return a random email"""
        return fake.email()

    @classmethod
    def password(cls):
        """return a random password"""
        return fake.password()

    @classmethod
    def user(
        cls,
        first_name=_Missing,
        last_name=_Missing,
        email=_Missing,
        password=_Missing,
        username=_Missing,
        save=True,
    ):
        """create a random user"""
        from cookgpt.auth.models import User

        return User.create(
            first_name=first_name
            if first_name is not _Missing
            else cls.first_name(),
            last_name=last_name
            if last_name is not _Missing
            else cls.last_name(),
            email=email if email is not _Missing else cls.email(),
            password=password if password is not _Missing else cls.password(),
            username=username if username is not _Missing else cls.username(),
            commit=save,
        )

    @classmethod
    def user_data(
        cls,
        first_name: Any = True,
        last_name: Any = True,
        email: Any = True,
        password: Any = True,
        username: Any = True,
    ):
        """return random user data"""
        data: "dict[str, str]" = {}
        if first_name is not False:
            data["first_name"] = (
                first_name if first_name is not True else cls.first_name()
            )
        if last_name is not False:
            data["last_name"] = (
                last_name if last_name is not True else cls.last_name()
            )
        if email is not False:
            data["email"] = email if email is not True else cls.email()
        if password is not False:
            data["password"] = (
                password if password is not True else cls.password()
            )
        if username is not False:
            data["username"] = (
                username if username is not True else cls.username()
            )
        return data

    @classmethod
    def chat(
        cls,
        content=_Missing,
        cost=_Missing,
        chat_type=_Missing,
        thread_id=_Missing,
        previous_chat_id=_Missing,
        sent_time=_Missing,
        order=_Missing,
        save=True,
    ):
        """create a random chat"""
        from random import choice
        from uuid import uuid4

        from cookgpt.chatbot.models import Chat

        return Chat.create(
            content=content if content is not _Missing else fake.text(),
            cost=cost if cost is not _Missing else fake.pyint(),
            chat_type=chat_type
            if chat_type is not _Missing
            else choice((MessageType.QUERY, MessageType.RESPONSE)),
            thread_id=thread_id if thread_id is not _Missing else uuid4(),
            previous_chat_id=previous_chat_id
            if previous_chat_id is not _Missing
            else None,
            sent_time=sent_time if sent_time is not _Missing else utcnow(),
            order=order if order is not _Missing else 0,
            commit=save,
        )


def extract_cookie(response, name):
    """
    Extract's a set cookie from a server response

    Args:
        response: a flask response
        name: the case-insensitive name of the cookie
    """
    for key, value in response.headers:
        if key.lower() == "set-cookie":
            cookies = value.split(";")
            for cookie in cookies:
                parts = cookie.split("=")
                if parts[0].strip().lower() == name.lower():
                    return parts[1].strip()
    return None


def extract_access_token(response):
    """extract access token from response"""

    return response.headers["Set-Cookie"].split(";")[0].split("=")[1]
