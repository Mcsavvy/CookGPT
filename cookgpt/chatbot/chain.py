from datetime import datetime as dt
from datetime import timezone as tz
from typing import Any, Dict, Union
from uuid import UUID

from langchain.callbacks import OpenAICallbackHandler
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import openai_callback_var
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI, FakeListChatModel
from langchain.chat_models.base import BaseChatModel
from langchain.schema import LLMResult
from langchain.schema.prompt_template import BasePromptTemplate
from pydantic import Field, root_validator

from cookgpt.chatbot.context import (
    chat_cost_ctx,
    memory_ctx,
    query_time_ctx,
    response_time_ctx,
)
from cookgpt.chatbot.data.fake_data import responses
from cookgpt.chatbot.data.prompts import prompt as PROMPT
from cookgpt.chatbot.memory import BaseMemory, ThreadMemory
from cookgpt.ext.config import config

Callbacks = Union[list[BaseCallbackHandler], None]


def get_llm_callbacks() -> "Callbacks":  # pragma: no cover
    """returns the callbacks for the chain"""
    return []


def get_chain_callbacks() -> "Callbacks":  # pragma: no cover
    """returns the callbacks for the chain"""
    return []


def get_llm() -> BaseChatModel:  # pragma: no cover
    """returns the language model"""
    if config.USE_OPENAI:
        return LLM()
    return FakeListChatModel(responses=responses)


def get_chain_input_key() -> str:
    """returns the input key for the chain"""
    return config.CHATBOT_CHAIN_INPUT_KEY


class ChatCallbackHandler(OpenAICallbackHandler):
    """tracks the cost and time of the conversation"""

    def on_chain_start(self, *args, **kwargs) -> Any:
        """tracks the time the query was sent"""
        query_time_ctx.set(dt.now(tz.utc))
        return super().on_chain_start(*args, **kwargs)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """tracks the cost of the conversation"""
        response_time_ctx.set(dt.now(tz.utc))
        super().on_llm_end(response, **kwargs)
        llm_output = response.llm_output
        if not llm_output or "token_usage" not in llm_output:
            return None
        token_usage = llm_output["token_usage"]  # pragma: no cover
        chat_cost_ctx.set(  # pragma: no cover
            (
                token_usage.get("prompt_tokens", 0),
                token_usage.get("completion_tokens", 0),
            )
        )

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any
    ) -> Any:
        """tracks the time the response was received"""
        if not response_time_ctx.get():  # pragma: no cover
            response_time_ctx.set(dt.now(tz.utc))
        return super().on_chain_end(
            outputs, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def register(self) -> None:  # pragma: no cover
        """register the callback handler"""
        openai_callback_var.set(self)

    def unregister(self) -> None:  # pragma: no cover
        """unregister the callback handler"""
        openai_callback_var.set(None)


class LLM(ChatOpenAI):
    """language model for the chatbot"""

    # callbacks: Callbacks = Field(default_factory=get_llm_callbacks)


class ThreadChain(ConversationChain):
    """custom chain for the language model"""

    input_key: str = Field(default_factory=get_chain_input_key)
    llm: BaseChatModel = Field(default_factory=get_llm)
    prompt: BasePromptTemplate = PROMPT
    memory: BaseMemory = Field(default_factory=ThreadMemory)
    # callbacks: Callbacks = Field(default_factory=get_chain_callbacks)

    # def __setattr__(self, name, value):
    #     if name == "memory":  # pragma: no cover
    #         callbacks = (cast(Callbacks, self.llm.callbacks) or []) + (
    #             self.callbacks or []
    #         )
    #         for cb in callbacks:  # type: ignore
    #             if hasattr(cb, "_memory"):
    #                 setattr(cb, "_memory", value)
    #     return super().__setattr__(name, value)

    @root_validator
    def set_context(cls, values):
        """set context"""
        memory_ctx.set(values["memory"])
        return values

    def reload(self):
        """reload variables"""
        self.input_key = get_chain_input_key()
        self.llm = get_llm()

    def predict(self, callbacks: Callbacks = None, **kwargs: Any) -> str:
        """predict the next response"""
        from langchain.schema import HumanMessage

        # ensure that the input key is provided
        assert config.CHATBOT_CHAIN_INPUT_KEY in kwargs, (
            "Please provide a value for the input key "
            f"({config.CHATBOT_CHAIN_INPUT_KEY})."
        )

        input: str = kwargs[config.CHATBOT_CHAIN_INPUT_KEY]
        kwargs[config.CHATBOT_CHAIN_INPUT_KEY] = [HumanMessage(content=input)]
        callbacks = (callbacks or []) + (callbacks_ctx.get() or [])
        print("callbacks:", callbacks)
        return super().predict(callbacks, **kwargs)
