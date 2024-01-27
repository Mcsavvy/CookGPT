"""Chain for the chatbot."""

from collections.abc import Iterator
from typing import Any, cast

import pydantic.v1 as pydantic_v1
from langchain.callbacks.base import Callbacks
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.chains import ConversationChain
from langchain.chat_models.base import BaseChatModel
from langchain.schema.output import ChatGenerationChunk, ChatResult
from langchain.schema.prompt_template import BasePromptTemplate
from langchain_community.chat_models import ChatOpenAI, FakeListChatModel
from langchain_core.messages import BaseMessage

from cookgpt import logging
from cookgpt.chatbot.data.fake_data import responses
from cookgpt.chatbot.data.prompts import prompt
from cookgpt.chatbot.memory import BaseMemory, ThreadMemory
from cookgpt.ext.config import config
from cookgpt.globals import getvar, setvar


def get_llm() -> BaseChatModel:  # pragma: no cover
    """Returns the language model."""
    llm_cls: type[LLM | FakeLLM]
    if config.USE_OPENAI:
        llm_cls = LLM
    else:
        llm_cls = FakeLLM
    return llm_cls(streaming=config.OPENAI_STREAMING)


def get_chain_input_key() -> str:
    """Returns the input key for the chain."""
    return config.CHATBOT_CHAIN_INPUT_KEY


class FakeLLM(FakeListChatModel):
    """Fake language model for the chatbot."""

    streaming: bool
    responses: list = responses
    i: int = 0

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        for c in super()._stream(messages, stop, run_manager, **kwargs):
            yield c
            if run_manager:
                content = cast(str, c.message.content)
                run_manager.on_llm_new_token(content)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self.streaming:
            logging.debug("Streaming FakeLLM...")
            generation: ChatGenerationChunk | None = None
            for chunk in self._stream(messages, stop, run_manager, **kwargs):
                if generation is None:
                    generation = chunk
                else:
                    generation += chunk
            assert generation is not None
            return ChatResult(generations=[generation])
        else:  # pragma: no cover
            logging.debug("Generating FakeLLM...")
            return super()._generate(messages, stop, run_manager, **kwargs)


class LLM(ChatOpenAI):
    """Language model for the chatbot."""


class ThreadChain(ConversationChain):
    """Chain for the chatbot."""

    input_key: str = pydantic_v1.Field(default_factory=get_chain_input_key)
    llm: "BaseChatModel" = pydantic_v1.Field(default_factory=get_llm)
    prompt: "BasePromptTemplate" = prompt
    memory: "BaseMemory" = pydantic_v1.Field(default_factory=ThreadMemory)

    @pydantic_v1.root_validator
    @classmethod
    def set_context(cls, values):
        """Set context."""
        setvar("memory", values["memory"])
        return values

    def reload(self):  # pragma: no cover
        """Reload the chain."""
        self.input_key = get_chain_input_key()
        self.llm = get_llm()

    def __call__(
        self,
        inputs: dict[str, Any] | Any,
        return_only_outputs: bool = False,
        callbacks: Callbacks = None,
        *,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        include_run_info: bool = False,
    ) -> dict[str, Any]:
        """Call the chain."""
        from langchain.schema import HumanMessage

        from cookgpt.chatbot.models import Chat

        # ensure that the input key is provided
        assert config.CHATBOT_CHAIN_INPUT_KEY in inputs, (
            "Please provide a value for the input key "
            f"({config.CHATBOT_CHAIN_INPUT_KEY})."
        )

        input: str = inputs[config.CHATBOT_CHAIN_INPUT_KEY]
        msg = HumanMessage(content=input)
        # set the id of the query
        if (query := getvar("query", Chat, None)) is not None:
            msg.additional_kwargs["id"] = query.pk
        inputs[config.CHATBOT_CHAIN_INPUT_KEY] = [msg]

        return super().__call__(
            inputs,
            return_only_outputs,
            callbacks,
            tags=tags,
            metadata=metadata,
            include_run_info=include_run_info,
        )

    @property
    def _chain_type(self) -> str:  # pragma: no cover
        return "thread_chain"
