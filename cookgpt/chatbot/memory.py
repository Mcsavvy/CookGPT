"""Chatbot memory module."""
import datetime
from collections.abc import Iterable
from typing import Any, cast

import pydantic.v1 as pydantic_v1
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories.in_memory import (
    ChatMessageHistory,
)
from langchain.schema import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    get_buffer_string,
)

from cookgpt import logging
from cookgpt.chatbot.models import Chat, MessageType
from cookgpt.ext.config import config
from cookgpt.globals import (
    chat_cost,
    getvar,
    query,
    resetvar,
    response,
    setvar,
    thread,
    user,
)


def get_memory_key() -> str:
    """Get chat memory key."""
    return config["CHATBOT_MEMORY_KEY"]


def get_human_prefix() -> str:  # pragma: no cover
    """Get chat memory human prefix."""
    return config["CHATBOT_MEMORY_HUMAN_PREFIX"]


def get_ai_prefix() -> str:  # pragma: no cover
    """Get chat memory ai prefix."""
    return config["CHATBOT_MEMORY_AI_PREFIX"]


def get_memory_input_key() -> str:
    """Get chat memory input key."""
    return config["CHATBOT_CHAIN_INPUT_KEY"]


class SingleThreadHistory(ChatMessageHistory, pydantic_v1.BaseModel):
    """A conversation thread backed memory."""

    @property
    def query_cost(self) -> int:
        """Return query cost."""
        return chat_cost[0]

    @property
    def response_cost(self) -> int:
        """Return response cost."""
        return chat_cost[1]

    def __getattribute__(self, __name: str) -> Any:
        """Get attribute."""
        if __name == "messages":
            setattr(self, __name, self.get_messages())
        return super().__getattribute__(__name)

    def get_messages(self) -> "list[BaseMessage]":  # pragma: no cover
        """Get all messages in thread."""
        chats: "list[BaseMessage]" = []
        # non-empty chats
        chats_query = Chat.query.filter(
            Chat.thread_id == thread.id, Chat.content != ""
        )
        for chat in cast(Iterable[Chat], chats_query):
            msg_cls = (
                HumanMessage
                if chat.chat_type == MessageType.QUERY
                else AIMessage
            )
            chats.append(
                msg_cls(
                    content=chat.content, additional_kwargs={"id": chat.pk}
                )
            )
        return chats

    def add_user_message(self, message: str) -> None:  # type: ignore[override]
        """Add the user's query to the database."""
        logging.debug("Adding user message to database...")
        extra: dict[str, Any] = {"cost": self.query_cost}
        if q_time := getvar("query_time", datetime.datetime):
            extra["sent_time"] = q_time
            resetvar("query_time")
        assert query.thread_id == thread.id, (
            "The query being added to the thread does not "
            "belong to the thread."
        )
        query.update(content=message, **extra)
        return None

    def add_ai_message(self, message: str) -> None:  # type: ignore[override]
        """Add the ai's response to the database."""
        logging.debug("Adding ai message to database...")
        extra: dict[str, Any] = {"cost": self.response_cost}
        if r_time := getvar("response_time", datetime.datetime):
            extra["sent_time"] = r_time
            resetvar("response_time")
        assert response, "No response found in context."
        assert response.thread_id == thread.id, (
            "The response being added to the thread does not "
            "belong to the thread."
        )
        response.update(content=message, **extra)

    def clear(self) -> None:  # pragma: no cover
        """Clear all messages in the thread."""
        return thread.clear()


class BaseMemory(ConversationBufferMemory):
    """A conversation memory that is user-aware."""

    memory_key: str = pydantic_v1.Field(default_factory=get_memory_key)
    input_key: str = pydantic_v1.Field(default_factory=get_memory_input_key)
    human_prefix: str = pydantic_v1.Field(default_factory=get_human_prefix)
    ai_prefix: str = pydantic_v1.Field(default_factory=get_ai_prefix)

    @property
    def user(self) -> str:
        """Return current user's name."""
        return user.first_name

    @pydantic_v1.root_validator
    @classmethod
    def set_context(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Set context for memory."""
        setvar("history", values["chat_memory"])
        return values

    @property
    def buffer_as_str(self) -> str:  # pragma: no cover
        """Return buffer as string."""
        return get_buffer_string(
            self.chat_memory.messages,
            human_prefix=self.human_prefix,
            ai_prefix=self.ai_prefix,
        )

    @property
    def memory_variables(self) -> "list[str]":
        """Return list of memory variables."""
        return [self.memory_key, "user"]

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Return chat thread and user's name."""
        logging.debug("Loading memory variables...")
        return {"user": self.user, self.memory_key: self.buffer_as_messages}


class ThreadMemory(BaseMemory):
    """A conversation thread memory."""

    chat_memory: "SingleThreadHistory" = pydantic_v1.Field(
        default_factory=SingleThreadHistory
    )
    return_message: bool = False

    def save_context(
        self, inputs: dict[str, Any], outputs: dict[str, str]
    ) -> None:
        """Save context from this conversation to database."""
        input = inputs[self.input_key]
        if isinstance(input, list):
            input = input[0]
        if isinstance(input, BaseMessage):
            input = input.content
        inputs[self.input_key] = input
        super().save_context(inputs, outputs)
        resetvar("chat_cost")
