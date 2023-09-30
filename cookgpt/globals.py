from contextvars import ContextVar, Token
from typing import TYPE_CHECKING, Optional, Type, TypeVar, overload

from flask.globals import _no_app_msg
from werkzeug.local import LocalProxy

from cookgpt import logging

if TYPE_CHECKING:
    from datetime import datetime

    from redis import Redis  # type: ignore

    from cookgpt.auth.models import User
    from cookgpt.chatbot.chain import ThreadChain
    from cookgpt.chatbot.memory import BaseMemory, SingleThreadHistory
    from cookgpt.chatbot.models import Chat, Thread


T = TypeVar("T")
Missing = object()


_tokens: dict[ContextVar[T], Token[T]] = {}  # type: ignore


_user_var: ContextVar["User"] = ContextVar("user")
_chain_var: ContextVar["ThreadChain"] = ContextVar("chain")
_thread_var: ContextVar["Thread"] = ContextVar("thread")
_memory_var: ContextVar["BaseMemory"] = ContextVar("memory")
_history_var: ContextVar["SingleThreadHistory"] = ContextVar("history")
_chat_cost_var: ContextVar["tuple[int, int]"] = ContextVar(
    "chat_cost", default=(0, 0)
)
_query_time_var: ContextVar["Optional[datetime]"] = ContextVar(
    "query_time", default=None
)
_response_time_var: ContextVar["Optional[datetime]"] = ContextVar(
    "response_time", default=None
)
_query_var: ContextVar["Chat"] = ContextVar("query")
_response_var: ContextVar["Chat"] = ContextVar("response")
_redis_var: "ContextVar[Redis]" = ContextVar("redis")


chain: "ThreadChain" = LocalProxy(_chain_var)  # type: ignore[assignment]
redis: "Redis" = LocalProxy(  # type: ignore[assignment]
    _redis_var, unbound_message=_no_app_msg
)
thread: "Thread" = LocalProxy(_thread_var)  # type: ignore[assignment]
memory: "BaseMemory" = LocalProxy(_memory_var)  # type: ignore[assignment]
history: "SingleThreadHistory" = LocalProxy(  # type: ignore[assignment]
    _history_var
)
user: "User" = LocalProxy(_user_var)  # type: ignore[assignment]
query_time: "Optional[datetime]" = LocalProxy(  # type: ignore[assignment]
    _query_time_var
)
response_time: "Optional[datetime]" = LocalProxy(  # type: ignore[assignment]
    _response_time_var
)
query: "Chat" = LocalProxy(_query_var)  # type: ignore[assignment]
response: "Chat" = LocalProxy(_response_var)  # type: ignore[assignment]
chat_cost: "tuple[int, int]" = LocalProxy(  # type: ignore[assignment]
    _chat_cost_var
)


def setvar(var: "ContextVar[T] | str", value: "T") -> None:
    """set context variable"""
    logging.debug(f"Setting context variable {var!r} to {value!r}")
    if isinstance(var, str):
        if not var.startswith("_"):
            var = "_" + var
        if not var.endswith("_var"):
            var += "_var"
        var = globals()[var]
    assert isinstance(var, ContextVar)
    _tokens[var] = var.set(value)


def resetvar(var: "ContextVar[T] | str") -> None:
    """reset context variable"""
    logging.debug(f"Resetting context variable {var!r}")
    if isinstance(var, str):
        if not var.startswith("_"):
            var = "_" + var
        if not var.endswith("_var"):
            var += "_var"
        var = globals()[var]
    assert isinstance(var, ContextVar)
    if var in _tokens:
        var.reset(_tokens[var])
        del _tokens[var]
    else:  # pragma: no cover
        raise RuntimeError(f"Cannot reset unset context variable {var!r}")


@overload
def getvar(var: ContextVar[T], _default: T) -> T:
    ...


@overload
def getvar(var: str, _type: Type[T]) -> T:
    ...


@overload
def getvar(var: str, _default: T) -> T:
    ...


def getvar(var, _type=None, _default=Missing):
    """get context variable"""
    logging.debug(f"Getting context variable {var}")
    if isinstance(var, str):
        if not var.startswith("_"):
            var = "_" + var
        if not var.endswith("_var"):
            var += "_var"
        var = globals()[var]
    assert isinstance(var, ContextVar)
    if _default is not Missing:  # pragma: no cover
        return var.get(_default)
    return var.get()


__all__ = [
    "setvar",
    "resetvar",
    "getvar",
    "chain",
    "redis",
    "thread",
    "memory",
    "history",
    "user",
    "query_time",
    "response_time",
    "query",
    "response",
    "chat_cost",
]
