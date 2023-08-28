from typing import Sequence

import tiktoken
from langchain.adapters.openai import convert_message_to_dict
from langchain.schema import BaseMessage


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


def convert_messages_to_dict(messages: Sequence[BaseMessage]):
    """Converts a list of messages to a list of dicts."""
    return [convert_message_to_dict(message) for message in messages]
