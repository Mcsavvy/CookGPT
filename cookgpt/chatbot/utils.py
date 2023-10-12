from contextlib import contextmanager
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, Sequence
from uuid import UUID, uuid4

import tiktoken

from cookgpt.chatbot.data.enums import MessageType
from cookgpt.chatbot.models import Thread
from cookgpt.ext.database import db
from cookgpt.utils import abort

if TYPE_CHECKING:
    from cookgpt.auth.models import User
    from cookgpt.chatbot.callback import ChatCallbackHandler
    from cookgpt.chatbot.models import Chat


def num_tokens_from_messages(
    messages: Sequence[dict], model="gpt-3.5-turbo-0613"
):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:  # pragma: no cover
        encoding = tiktoken.get_encoding("cl100k_base")
    if (
        model == "gpt-3.5-turbo-0613"
    ):  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            # every message follows <im_start>{role/name}\n{content}<im_end>\n
            num_tokens += 4
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                # if there's a name, the role is omitted
                if key == "name":  # pragma: no cover
                    num_tokens += (
                        -1
                    )  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(
            (
                "num_tokens_from_messages() is not presently "
                f"implemented for model {model}."
            )
        )


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
