from typing import TYPE_CHECKING

from cookgpt.auth.models import User
from cookgpt.chatbot.chain import ThreadChain
from cookgpt.chatbot.utils import get_chat_callback  # noqa
from cookgpt.globals import setvar

if TYPE_CHECKING:
    from cookgpt.app import App


chain = ThreadChain()


def test_chat_memory():
    admin = User.query.first()
    thread = admin.default_thread
    handler = get_chat_callback()
    handler.verbose = True
    setvar("chain", chain)
    setvar("user", admin)
    setvar("thread", thread)
    handler.register()

    return {
        "admin": admin,
        "thread": thread,
        "memory": chain.memory,
        "chain": chain,
        "handler": handler,
    }


def init_app(app: "App"):
    app.shell_context_processor(test_chat_memory)
