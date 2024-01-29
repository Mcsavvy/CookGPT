"""Chatbot API Blueprint."""

from apiflask import APIBlueprint

from cookgpt import docs

app = APIBlueprint(
    "chatbot",
    __name__,
    url_prefix="/chat",
    cli_group="chat",
    tag={"name": "chat", "description": docs.CHAT},
)


from cookgpt.chatbot import cli, views  # noqa: E402, F401
from cookgpt.chatbot.models import Chat, Thread  # noqa: E402, F401
