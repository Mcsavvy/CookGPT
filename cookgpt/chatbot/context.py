from contextvars import ContextVar
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from datetime import datetime

    from cookgpt.auth.models import User
    from cookgpt.chatbot.chain import Chain
    from cookgpt.chatbot.memory import BaseMemory, SingleThreadHistory
    from cookgpt.chatbot.models import Thread

user_ctx: ContextVar["User"] = ContextVar("user_ctx")
chain_ctx: ContextVar["Chain"] = ContextVar("chain_ctx")
thread_ctx: ContextVar["Thread"] = ContextVar("thread_ctx")
memory_ctx: ContextVar["BaseMemory"] = ContextVar("memory_ctx")
history_ctx: ContextVar["SingleThreadHistory"] = ContextVar("history_ctx")
chat_cost_ctx: ContextVar["tuple[int, int]"] = ContextVar(
    "chat_cost_ctx", default=(0, 0)
)
query_time_ctx: ContextVar["Optional[datetime]"] = ContextVar(
    "query_time_ctx", default=None
)
response_time_ctx: ContextVar["Optional[datetime]"] = ContextVar(
    "response_time_ctx", default=None
)
