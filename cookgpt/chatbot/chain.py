from datetime import datetime as dt
from datetime import timezone as tz
from typing import Any, Dict, List, cast
from uuid import UUID

from langchain.adapters.openai import convert_message_to_dict
from langchain.callbacks import (
    OpenAICallbackHandler,
    StreamingStdOutCallbackHandler,
)
from langchain.callbacks.base import BaseCallbackManager, Callbacks
from langchain.callbacks.openai_info import get_openai_token_cost_for_model
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI, FakeListChatModel
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseMessage, ChatGeneration, LLMResult
from langchain.schema.prompt_template import BasePromptTemplate
from pydantic import Field, root_validator

from cookgpt.chatbot.context import (
    callbacks_ctx,
    chat_cost_ctx,
    memory_ctx,
    query_time_ctx,
    response_time_ctx,
)
from cookgpt.chatbot.data.fake_data import responses
from cookgpt.chatbot.data.prompts import prompt as PROMPT
from cookgpt.chatbot.memory import BaseMemory, ThreadMemory
from cookgpt.chatbot.utils import convert_messages_to_dict  # noqa
from cookgpt.chatbot.utils import num_tokens_from_messages
from cookgpt.ext.config import config


def get_llm_callbacks() -> "Callbacks":  # pragma: no cover
    """returns the callbacks for the chain"""
    if config.LANGCHAIN_VERBOSE:
        return [StreamingStdOutCallbackHandler()]
    return []


def get_chain_callbacks() -> "Callbacks":  # pragma: no cover
    """returns the callbacks for the chain"""
    return []


def get_llm() -> BaseChatModel:  # pragma: no cover
    """returns the language model"""
    if config.USE_OPENAI:
        return LLM(
            streaming=config.OPENAI_STREAMING,
            callbacks=get_llm_callbacks(),
        )
    return FakeListChatModel(responses=responses)


def get_chain_input_key() -> str:
    """returns the input key for the chain"""
    return config.CHATBOT_CHAIN_INPUT_KEY


class ChatCallbackHandler(OpenAICallbackHandler):
    """tracks the cost and time of the conversation"""

    def compute_completion_tokens(self, result: LLMResult, model_name: str):
        """Compute the cost of the result."""
        ai_message = cast(ChatGeneration, result.generations[0][0]).message
        ai_message_raw = convert_message_to_dict(ai_message)
        num_tokens = num_tokens_from_messages([ai_message_raw], model_name)
        completion_cost = get_openai_token_cost_for_model(
            model_name, num_tokens, is_completion=True
        )
        self.total_tokens += num_tokens
        self.completion_tokens += num_tokens
        self.total_cost += completion_cost

        cost = chat_cost_ctx.get()
        chat_cost_ctx.set((cost[0], num_tokens))

    def compute_prompt_tokens(
        self, messages: List[BaseMessage], model_name: str
    ):
        """Compute the cost of the prompt."""
        messages_raw = convert_messages_to_dict(messages)
        num_tokens = num_tokens_from_messages(messages_raw, model_name)
        prompt_cost = get_openai_token_cost_for_model(model_name, num_tokens)
        self.total_tokens += num_tokens
        self.prompt_tokens += num_tokens
        self.total_cost += prompt_cost

        cost = chat_cost_ctx.get()
        chat_cost_ctx.set((num_tokens, cost[1]))

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: List[str] | None = None,
        metadata: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """tracks the time the query was sent"""
        query_time_ctx.set(dt.now(tz.utc))

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """tracks the cost of the conversation"""
        response_time_ctx.set(dt.now(tz.utc))
        super().on_llm_end(response, **kwargs)
        llm_output = response.llm_output
        if (
            not llm_output or "token_usage" not in llm_output
        ) and config.OPENAI_STREAMING:
            self.compute_completion_tokens(response, "gpt-3.5-turbo-0613")
            self.successful_requests += 1
            return
        assert llm_output and "token_usage" in llm_output, (
            "The LLM response did not contain a token_usage "
            "field, but the LLM was not streaming."
        )
        token_usage = llm_output["token_usage"]  # pragma: no cover
        chat_cost_ctx.set(  # pragma: no cover
            (
                token_usage.get("prompt_tokens", 0),
                token_usage.get("completion_tokens", 0),
            )
        )
        self.successful_requests += 1  # pragma: no cover

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: List[str] | None = None,
        metadata: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """tracks the cost of the prompt"""
        if config.OPENAI_STREAMING:
            return self.compute_prompt_tokens(
                messages[0], "gpt-3.5-turbo-0613"
            )

    def register(self) -> None:  # pragma: no cover
        """register the callback handler"""
        callbacks_ctx.set([self])

    def unregister(self) -> None:  # pragma: no cover
        """unregister the callback handler"""
        callbacks_ctx.set(None)


class LLM(ChatOpenAI):
    """language model for the chatbot"""

    # callbacks: Callbacks = Field(default_factory=get_llm_callbacks)


class ThreadChain(ConversationChain):
    """custom chain for the language model"""

    input_key: str = Field(default_factory=get_chain_input_key)
    llm: "BaseChatModel" = Field(default_factory=get_llm)
    prompt: "BasePromptTemplate" = PROMPT
    memory: "BaseMemory" = Field(default_factory=ThreadMemory)

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
        if isinstance(callbacks, BaseCallbackManager):  # pragma: no cover
            for cb in callbacks_ctx.get() or []:
                callbacks.add_handler(cb, inherit=True)
        elif callbacks is None:
            callbacks = callbacks_ctx.get() or []
        else:
            callbacks.extend(callbacks_ctx.get() or [])
        return super().predict(callbacks, **kwargs)

    @property
    def _chain_type(self) -> str:  # pragma: no cover
        return "thread_chain"
