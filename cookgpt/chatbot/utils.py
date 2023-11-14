from contextlib import contextmanager
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, Sequence, cast
from uuid import UUID, uuid4

import tiktoken
from langchain.adapters import openai
from langchain.schema.messages import BaseMessage

from cookgpt import logging
from cookgpt.chatbot.data.enums import MessageType
from cookgpt.chatbot.models import Thread
from cookgpt.ext.cache import cache
from cookgpt.ext.database import db
from cookgpt.utils import abort

if TYPE_CHECKING:
    from cookgpt.auth.models import User
    from cookgpt.chatbot.callback import ChatCallbackHandler
    from cookgpt.chatbot.models import Chat

encoding = tiktoken.get_encoding("cl100k_base")


def num_tokens_from_messages(
    messages: Sequence[dict], model="gpt-3.5-turbo-0613"
):
    """Returns the number of tokens used by a list of messages."""
    num_tokens = 0
    for message in messages:
        cost = 4
        # every message follows <im_start>{role/name}\n{content}<im_end>\n
        if "id" in message:
            if cache.has(f"chat:{message['id']}:cost"):
                logging.debug("Using cached cost for %s", message["id"][:6])
                num_tokens += cast(
                    int, cache.get(f"chat:{message['id']}:cost")
                )
                continue  # pragma: no cover
            logging.debug("Computing cost for %s", message["id"][:6])
        else:
            logging.debug("Computing cost for unsaved message")
        for key, value in message.items():
            cost += len(encoding.encode(value))
            if key == "name":  # pragma: no cover
                cost += -1  # role is always required and always 1 token
        if "id" in message:
            cache.set(f"chat:{message['id']}:cost", cost, timeout=0)
        num_tokens += cost
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


def convert_message_to_dict(message: "BaseMessage") -> dict:
    """convert message to dict"""
    converted = openai.convert_message_to_dict(message)
    if "id" in message.additional_kwargs:
        converted["id"] = message.additional_kwargs["id"]
    return converted


def get_stream_name(user: "User", chat: "Chat") -> str:
    """Returns the stream name for a given user and chat."""
    return f"stream:{chat.id.hex}"


def get_chat_callback():  # pragma: no cover
    """returns the callbacks for the chain"""
    from cookgpt.chatbot.callback import ChatCallbackHandler

    return ChatCallbackHandler()


@contextmanager
def use_chat_callback(cb: "Optional[ChatCallbackHandler]" = None):
    """use chat callback"""

    cb = cb or get_chat_callback()
    try:
        cb.register()
        yield cb
    finally:
        cb.unregister()


def get_thread(thread_id: str | UUID, required=True):
    """Get a thread using it's ID"""
    if isinstance(thread_id, str):  # pragma: no cover
        thread_id = UUID(thread_id)
    thread = db.session.get(Thread, thread_id)
    if not thread and required:  # pragma: no cover
        abort(404, "Thread not found")
    return thread


def make_dummy_chat(
    response: str,
    id: Optional[UUID] = None,
    previous_chat_id: Optional[UUID] = None,
    next_chat_id: Optional[UUID] = None,
    thread_id: Optional[UUID] = None,
    sent_time: Optional[datetime] = None,
    chat_type: MessageType = MessageType.RESPONSE,
    cost: int = 0,
    streaming: bool = False,
):
    """make fake response"""

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
