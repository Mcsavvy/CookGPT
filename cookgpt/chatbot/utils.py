"""Chatbot utilities."""

from collections.abc import Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal, cast
from uuid import UUID, uuid4

import tiktoken
from langchain.adapters import openai
from langchain.schema.messages import BaseMessage

from cookgpt import logging
from cookgpt.chatbot.data.enums import MessageType
from cookgpt.chatbot.models import Thread
from cookgpt.ext.cache import cache
from cookgpt.ext.database import db
from cookgpt.globals import getvar
from cookgpt.utils import abort

if TYPE_CHECKING:
    from cookgpt.auth.models import User
    from cookgpt.chatbot.callback import ChatCallbackHandler
    from cookgpt.chatbot.models import Chat

encoding = tiktoken.get_encoding("cl100k_base")


def _get_msg_cost_from_cache(id: str) -> int:
    """Get message cost from cache."""
    cache_key = f"chat:{id}:cost"
    if cache.has(cache_key):
        logging.debug("Using cached message cost for chat %r", id[:6])
        return cast(int, cache.get(cache_key))
    return 0


def _set_msg_cost_in_cache(id: str, cost: int):
    """Set message cost in cache."""
    cache_key = f"chat:{id}:cost"
    logging.debug("Caching cost for message %r", id[:6])
    cache.set(cache_key, cost, timeout=0)


def _get_system_msg_cost_from_cache(user: "User") -> int:
    """Get system message cost from cache."""
    cache_key = f"system_msg:{user.uid}:cost"
    if cache.has(cache_key):
        logging.debug(
            "Using cached system message cost for user %r", user.name
        )
        return cast(int, cache.get(cache_key))
    return 0


def _set_system_msg_cost_in_cache(user: "User", cost: int):
    """Set system message cost in cache."""
    cache_key = f"system_msg:{user.uid}:cost"
    logging.debug("Caching system message cost for user %r", user.name)
    cache.set(cache_key, cost, timeout=0)


def num_tokens_from_messages(
    messages: Sequence[dict], model="gpt-3.5-turbo-0613"
):
    """Returns the number of tokens used by a list of messages."""
    from cookgpt.auth.models import User

    num_tokens = 0
    user = getvar("user", _default=None, _type=User)
    for message in messages:
        role = cast(Literal["user", "assistant", "system"], message["role"])
        cost = 4

        # check if message is cached
        if "id" in message and (
            cost := _get_msg_cost_from_cache(message["id"])
        ):
            num_tokens += cost
            continue  # pragma: no cover

        # check if system message is cached
        elif (
            role == "system"
            and user
            and (cost := _get_system_msg_cost_from_cache(user))
        ):
            num_tokens += cost
            continue
        else:  # pragma: no cover
            if role == "system":
                logging.warning("Working outside of user context. ")
            else:
                logging.warning("ID not found in %s message.", role)
        for key, value in message.items():
            cost += len(encoding.encode(value))
            if key == "name":  # pragma: no cover
                cost += -1  # role is always required and always 1 token
        logging.debug("Computed cost for %s message: %s", role, cost)
        # cache the cost
        if "id" in message:
            _set_msg_cost_in_cache(message["id"], cost)
        # cache the system message cost
        if user and role == "system":
            _set_system_msg_cost_in_cache(user, cost)
        else:  # pragma: no cover
            logging.warning(
                "Unable to cache cost for %s message: %r", role, message
            )
        num_tokens += cost
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


def convert_message_to_dict(message: "BaseMessage") -> dict:
    """Convert message to dict."""
    converted = openai.convert_message_to_dict(message)
    if "id" in message.additional_kwargs:
        converted["id"] = message.additional_kwargs["id"]
    return converted


def get_stream_name(user: "User", chat: "Chat") -> str:
    """Returns the stream name for a given user and chat."""
    return f"stream:{chat.id.hex}"


def get_chat_callback():  # pragma: no cover
    """Returns the callbacks for the chain."""
    from cookgpt.chatbot.callback import ChatCallbackHandler

    return ChatCallbackHandler()


@contextmanager
def use_chat_callback(cb: "ChatCallbackHandler | None" = None):
    """Use chat callback."""
    cb = cb or get_chat_callback()
    try:
        cb.register()
        yield cb
    finally:
        cb.unregister()


def get_thread(thread_id: str | UUID, required=True):
    """Get a thread using it's ID."""
    if isinstance(thread_id, str):  # pragma: no cover
        thread_id = UUID(thread_id)
    thread = db.session.get(Thread, thread_id)
    if not thread and required:  # pragma: no cover
        abort(404, "Thread not found")
    return thread


def make_dummy_chat(
    response: str,
    id: UUID | None = None,
    previous_chat_id: UUID | None = None,
    next_chat_id: UUID | None = None,
    thread_id: UUID | None = None,
    sent_time: datetime | None = None,
    chat_type: MessageType = MessageType.RESPONSE,
    cost: int = 0,
    streaming: bool = False,
):
    """Make fake response."""
    return {
        "chat": {
            "id": id or uuid4(),
            "content": response,
            "chat_type": chat_type,
            "cost": cost,
            "previous_chat_id": previous_chat_id,
            "next_chat_id": next_chat_id,
            "sent_time": sent_time or datetime.now(tz=timezone.utc),
            "thread_id": thread_id or uuid4(),
        },
        "streaming": streaming,
    }
