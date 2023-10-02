from contextlib import contextmanager
from typing import TYPE_CHECKING, Optional, Sequence

import tiktoken

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
