"""
Since the APIs currently being used are stateless, it makes sense that
we create our own chat memory implementation and do that efficiently too.

SqlConversationMemory:
    this memory stores each input from the user and the output from
    the assistant in an SQL database augmented with Flask-SqlAlchemy
"""
from typing import Any, Dict, Iterable, cast

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
from pydantic import BaseModel, Field, root_validator

from cookgpt.chatbot.context import (
    chat_cost_ctx,
    history_ctx,
    query_time_ctx,
    response_time_ctx,
    thread_ctx,
    user_ctx,
)
from cookgpt.chatbot.models import Chat, MessageType, Thread
from cookgpt.ext.config import config


def get_memory_key() -> str:
    """get chat memory key"""
    return config["CHATBOT_MEMORY_KEY"]


def get_human_prefix() -> str:  # pragma: no cover
    """get chat memory human prefix"""
    return config["CHATBOT_MEMORY_HUMAN_PREFIX"]


def get_ai_prefix() -> str:  # pragma: no cover
    """get chat memory ai prefix"""
    return config["CHATBOT_MEMORY_AI_PREFIX"]


def get_memory_input_key() -> str:
    """get chat memory input key"""
    return config["CHATBOT_CHAIN_INPUT_KEY"]


class SingleThreadHistory(ChatMessageHistory, BaseModel):
    """An SqlAlchemy models backed chat history"""

    @property
    def thread(self) -> "Thread":
        """return current thread"""
        return thread_ctx.get()

    @property
    def query_cost(self) -> int:
        """return query cost"""
        return chat_cost_ctx.get()[0]

    @property
    def response_cost(self) -> int:
        """return response cost"""
        return chat_cost_ctx.get()[1]

    def _unset_query_cost(self) -> None:
        """delete query cost"""
        chat_cost_ctx.set((0, 0))

    def __getattribute__(self, __name: str) -> Any:
        if __name == "messages":
            setattr(self, __name, self.get_messages())
        return super().__getattribute__(__name)

    def get_messages(self) -> "list[BaseMessage]":  # pragma: no cover
        """get all messages in thread"""
        chats: "list[BaseMessage]" = []
        for chat in cast(Iterable[Chat], self.thread.chats):
            if chat.chat_type == MessageType.QUERY:
                chats.append(HumanMessage(content=chat.content))
            else:
                chats.append(AIMessage(content=chat.content))
        return chats

    def add_user_message(self, message: str) -> None:
        """add the user's query to the database"""
        extra: dict[str, Any] = {"cost": self.query_cost}
        if q_time := query_time_ctx.get():
            extra["sent_time"] = q_time
            query_time_ctx.set(None)
        self.thread.add_query(content=message, **extra)
        return None

    def add_ai_message(self, message: str) -> None:
        """add the ai's response to the database"""
        extra: dict[str, Any] = {"cost": self.response_cost}
        if r_time := response_time_ctx.get():
            extra["sent_time"] = r_time
            response_time_ctx.set(None)
        self.thread.add_response(content=message, **extra)
        return None

    def clear(self) -> None:  # pragma: no cover
        """Clear all messages in the thread"""
        return self.thread.clear()


class BaseMemory(ConversationBufferMemory):
    """
    A conversation memory that is user aware
    """

    memory_key: str = Field(default_factory=get_memory_key)
    input_key: str = Field(default_factory=get_memory_input_key)
    human_prefix: str = Field(default_factory=get_human_prefix)
    ai_prefix: str = Field(default_factory=get_ai_prefix)

    @property
    def user(self) -> str:
        """return current user's name"""
        return user_ctx.get().first_name

    @root_validator
    def set_context(cls, values):
        """set context"""
        history_ctx.set(values["chat_memory"])
        return values

    @property
    def buffer_as_str(self) -> str:  # pragma: no cover
        """return buffer as string"""
        return get_buffer_string(
            self.chat_memory.messages,
            human_prefix=self.human_prefix,
            ai_prefix=self.ai_prefix,
        )

    @property
    def memory_variables(self) -> "list[str]":
        """return list of memory variables"""
        return [self.memory_key, "user"]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """return chat thread and user's name"""
        return {"user": self.user, self.memory_key: self.buffer_as_messages}


class ThreadMemory(BaseMemory, BaseModel):
    """A conversation thread memory"""

    chat_memory: "SingleThreadHistory" = Field(
        default_factory=SingleThreadHistory
    )
    return_message: bool = False

    def save_context(
        self, inputs: Dict[str, Any], outputs: Dict[str, str]
    ) -> None:
        """Save context from this conversation to database."""
        input = inputs[self.input_key]
        if isinstance(input, list):
            input = input[0]
        if isinstance(input, BaseMessage):
            input = input.content
        inputs[self.input_key] = input
        super().save_context(inputs, outputs)
        self.chat_memory._unset_query_cost()
