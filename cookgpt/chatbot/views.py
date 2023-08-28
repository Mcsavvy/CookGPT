"""Chatbot views"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from typing import Optional as O
from uuid import UUID, uuid4

from apiflask.views import MethodView
from flask_jwt_extended import get_current_user, jwt_required

from cookgpt import docs
from cookgpt.chatbot import app
from cookgpt.chatbot.chain import ChatCallbackHandler, ThreadChain
from cookgpt.chatbot.context import chain_ctx, thread_ctx, user_ctx
from cookgpt.chatbot.data import examples as ex
from cookgpt.chatbot.data import schemas as sc
from cookgpt.chatbot.data.enums import MessageType
from cookgpt.chatbot.memory import get_memory_input_key
from cookgpt.chatbot.models import Chat
from cookgpt.utils import abort, api_output

if TYPE_CHECKING:
    from cookgpt.auth.models import User


chain = ThreadChain()
chain_ctx.set(chain)


def make_dummy_chat(
    response: str,
    id: O[UUID] = None,
    previous_chat_id: O[UUID] = None,
    next_chat_id: O[UUID] = None,
    thread_id: O[UUID] = None,
    sent_time: O[datetime] = None,
    chat_type: MessageType = MessageType.RESPONSE,
    cost: int = 0,
):
    """make fake response"""

    return {
        "id": id or uuid4(),
        "content": response,
        "chat_type": chat_type,
        "cost": cost,
        "previous_chat_id": previous_chat_id,
        "next_chat_id": next_chat_id,
        "sent_time": sent_time or datetime.now(tz=timezone.utc),
        "thread_id": thread_id or uuid4(),
    }


class ThreadView(MethodView):
    """thread endpoints"""

    decorators = [jwt_required()]

    @app.output(
        sc.Chats.Get,
        200,
        example=ex.GetChat.Out,
        description="All messages in the thread",
    )
    @app.doc(description=docs.CHAT_GET_CHATS)
    def get(self):
        """Get all messages in a thread."""
        # TODO: allow user to select thread
        user = get_current_user()
        thread = user.default_thread
        return {"chats": thread.chats}

    @app.output(
        sc.Chat.Delete,
        200,
        example=ex.DeleteChat.Out,
        description="Success message",
    )
    @app.doc(description=docs.CHAT_DELETE_CHATS)
    def delete(self):
        """Delete all messages in a thread."""
        # TODO: allow user to select thread
        user = get_current_user()
        thread = user.default_thread
        thread.clear()
        return {"message": "All chats deleted"}


class ChatView(MethodView):
    """Chat endpoints"""

    decorators = [jwt_required()]

    @app.output(
        sc.Chat.Out,
        200,
        example=ex.GetChat.Out,
        description="A single chat",
    )
    @app.doc(description=docs.CHAT_GET_CHAT)
    def get(self, chat_id):
        """Get a single chat from a thread."""
        # TODO: allow user to select thread
        user = get_current_user()
        thread = user.default_thread
        # chat = (
        #     Chat.query.join(Thread)
        #     .filter(Chat.id == chat_id, Thread.user_id == user.id)
        #     .first()
        # )
        chat = Chat.query.filter(
            Chat.id == chat_id, Chat.thread_id == thread.id
        ).first()
        if not chat:
            abort(404, "Chat not found")
        return chat

    @app.output(
        sc.Chat.Delete,
        200,
        example=ex.DeleteChat.Out,
        description="Success message",
    )
    @app.doc(description=docs.CHAT_DELETE_CHAT)
    def delete(self, chat_id):
        """Delete a single chat from a thread."""
        user = get_current_user()
        # chat = (
        #     Chat.query.join(Thread)
        #     .filter(Chat.id == chat_id, Thread.user_id == user.id)
        #     .first()
        # )
        chat = Chat.query.filter(
            Chat.id == chat_id, Chat.thread_id == user.default_thread.id
        ).first()
        if not chat:
            return {"message": "Chat not found"}, 404
        chat.delete()
        return {"message": "Chat deleted"}

    @app.input(
        sc.Chat.Send,
        example=ex.Chat.In,
    )
    @app.output(
        sc.Chat.Out,
        201,
        example=ex.Chat.Out,
        description="The chatbot's response",
    )
    @api_output(
        sc.Chat.Out,
        200,
        example=ex.Chat.Out,
        description="A dummy response",
    )
    @app.doc(description=docs.CHAT_POST_CHAT)
    def post(self, json_data: dict) -> Any:
        """Send a message to the chatbot."""

        chain.reload()
        input_key = get_memory_input_key()
        query: str = json_data["query"]
        user: "User" = get_current_user()
        user_ctx.set(user)

        # TODO: allow user to select thread
        thread = user.default_thread
        thread_ctx.set(thread)

        handler = ChatCallbackHandler()
        handler.register()

        if thread.cost >= user.max_chat_cost:
            return (
                make_dummy_chat(
                    "You don't have enough tokens to make this request.",
                    previous_chat_id=thread.last_chat.id
                    if thread.last_chat
                    else None,
                    thread_id=thread.id,
                ),
                200,
            )

        chain.predict(**{input_key: query})  # type: ignore
        return thread.last_chat, 201


app.add_url_rule(
    "/chat/<uuid:chat_id>",
    view_func=ChatView.as_view("chat"),
    methods=["GET", "DELETE"],
)
app.add_url_rule("/thread", view_func=ThreadView.as_view("thread"))
app.add_url_rule(
    "/chat", view_func=ChatView.as_view("query"), methods=["POST"]
)
