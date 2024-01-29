"""Chatbot chat views."""
from collections.abc import Generator
from time import sleep
from typing import TYPE_CHECKING, Any, TypeAlias
from uuid import UUID

from apiflask.views import MethodView
from flask import stream_with_context
from flask_jwt_extended import get_current_user

from cookgpt import docs, logging
from cookgpt.chatbot import app
from cookgpt.chatbot.data import examples as ex
from cookgpt.chatbot.data import schemas as sc
from cookgpt.chatbot.memory import get_memory_input_key
from cookgpt.chatbot.models import Chat
from cookgpt.chatbot.utils import get_stream_name, get_thread, make_dummy_chat
from cookgpt.ext import db
from cookgpt.ext.auth import auth_required
from cookgpt.ext.cache import (
    cache,
    chat_cache_key,
    chats_cache_key,
    threads_cache_key,
)
from cookgpt.utils import abort, api_output

if TYPE_CHECKING:
    from cookgpt.auth.models import User


StreamEntryT = dict[bytes, bytes | int]
StreamOutputT: TypeAlias = list[tuple[bytes, list[tuple[bytes, StreamEntryT]]]]


class ChatsView(MethodView):
    """chats endpoints."""

    decorators = [auth_required()]

    @app.input(
        sc.Chats.Get.QueryParams,
        example=ex.Chats.Get.QueryParams,
        location="query",
    )
    @app.output(
        sc.Chats.Get.Response,
        200,
        example=ex.Chats.Get.Response,
        description="All messages in the thread",
    )
    @api_output(
        sc.Thread.NotFound,
        404,
        example=ex.Thread.NotFound,
        description="An error when the specified thread is not found",
    )
    @app.doc(description=docs.CHAT_GET_CHATS)
    @cache.cached(timeout=0, make_cache_key=chats_cache_key)
    def get(self, query_data):
        """Get all messages in a thread."""
        logging.info("GET all chats from thread")
        thread = get_thread(query_data["thread_id"])
        logging.info("Using thread %s", thread.id)

        return {"chats": [sc.parse_chat(chat) for chat in thread.chats]}

    @app.input(sc.Chats.Delete.Body, example=ex.Chats.Delete.Body)
    @app.output(
        sc.Chats.Delete.Response,
        200,
        example=ex.Chat.Delete.Response,
        description="Success message",
    )
    @app.doc(description=docs.CHAT_DELETE_CHATS)
    def delete(self, json_data):
        """Delete all messages in a thread."""
        logging.info("DELETE all chats from thread")
        thread = get_thread(json_data["thread_id"])
        logging.info("Clearing thread %s", thread.id)
        thread.clear()

        return {"message": "All chats deleted"}


class ChatView(MethodView):
    """Chat endpoints."""

    decorators = [auth_required()]

    @app.output(
        sc.Chat.Get.Response,
        200,
        example=ex.Chat.Get.Response,
        description="A single chat",
    )
    @app.doc(description=docs.CHAT_GET_CHAT)
    @cache.cached(timeout=0, make_cache_key=chat_cache_key)
    def get(self, chat_id):
        """Get a single chat from a thread."""
        logging.info("GET chat %s", chat_id)
        get_current_user()
        chat = Chat.query.filter(Chat.id == chat_id).first()
        if not chat:
            abort(404, "Chat not found")
        return sc.parse_chat(chat)

    @app.output(
        sc.Chat.Delete.Response,
        200,
        example=ex.Chat.Delete.Response,
        description="Success message",
    )
    @app.doc(description=docs.CHAT_DELETE_CHAT)
    def delete(self, chat_id):
        """Delete a single chat from a thread."""
        logging.info("DELETE chat %s from thread", chat_id)
        chat = db.session.get(Chat, chat_id)
        if not chat:
            return {"message": "Chat not found"}, 404
        logging.info("Deleting from thread %s", chat.thread.id)
        chat.delete()
        return {"message": "Chat deleted"}

    @app.input(
        sc.Chat.Post.Body,
        example=ex.Chat.Post.Body,
    )
    @app.input(
        sc.Chat.Post.QueryParams,
        location="query",
        example=ex.Chat.Post.QueryParams,
    )
    @app.output(
        sc.Chat.Post.Response,
        201,
        example=ex.Chat.Post.Response,
        description="The chatbot's response",
    )
    @api_output(
        sc.Chat.Post.Response,
        200,
        example=ex.Chat.Post.Response,
        description="A dummy response",
    )
    @api_output(
        sc.Thread.NotFound,
        404,
        example=ex.Thread.NotFound,
        description="An error when the specified thread is not found",
    )
    @app.doc(description=docs.CHAT_POST_CHAT)
    def post(self, json_data: dict, query_data: dict) -> Any:
        """Send a message to the chatbot."""
        from cookgpt.chatbot.tasks import send_query
        from cookgpt.chatbot.utils import get_stream_name
        from cookgpt.globals import current_app as app
        from redisflow import celeryapp

        input_key = get_memory_input_key()
        query: str = json_data["query"]
        user: "User" = get_current_user()

        if "thread_id" in json_data:
            thread = get_thread(json_data["thread_id"])
        else:
            thread = user.create_thread(title="New Thread")
            cache.delete(threads_cache_key(user_id=user.pk))

        stream_response = query_data["stream"]

        if stream_response:
            logging.info("POST chat to thread (streamed)")
        else:
            logging.info("POST chat to thread")
        logging.info("Using thread %s", thread.id)
        if thread.cost >= user.max_chat_cost:
            return (
                make_dummy_chat(
                    "You don't have enough tokens to make this request.",
                    previous_chat_id=thread.last_chat.id
                    if thread.last_chat
                    else None,
                    thread_id=thread.id,
                    streaming=False,
                ),
                200,
            )
        q = thread.add_query("")
        r = thread.add_response("", previous_chat=q)
        stream = get_stream_name(user, r)
        app.redis.set(f"{stream}:status", "PENDING")
        if stream_response:
            # Run the task in the background
            logging.info("Sending query to AI in background")
            task = celeryapp.send_task(
                "chatbot.send_query",
                args=(q.id, r.id, thread.id, {input_key: query}),
            )
            app.redis.set(f"{stream}:task", task.id)
        else:
            # Run the task in the foreground
            logging.info("Sending query to AI in foreground")
            send_query(q.id, r.id, thread.id, {input_key: query})
            app.redis.set(f"{stream}:task", "")
        db.session.refresh(r)
        db.session.refresh(q)
        return {
            "chat": r,
            "streaming": stream_response,
        }, 201


def clear_stream(stream: str):
    """Clear a stream."""
    from cookgpt.globals import current_app as app

    logging.debug("Clearing stream %s", stream)
    app.redis.xtrim(stream, 0)


def stream_existing_chat(chat: Chat) -> Generator[str, Any, None]:
    """Stream an existing chat.

    Args:
        chat (Chat): the chat to stream
    Yields:
        str: a character from the chat
    """
    logging.debug("streaming existing chat %s", chat.id)
    yield from iter(chat.content)


def stream_from_redis(
    stream: str, entry_id: bytes = b"0-0"
) -> Generator[bytes, Any, None]:
    """Reads outputs from the AI via redis stream.

    Args:
        stream (str): the name of the redis stream
        entry_id (bytes): the entry to start reading from

    Yields:
        bytes: a token from the AI
    """
    from cookgpt.globals import current_app as app

    logging.debug("Streaming %r from %s", stream, entry_id)
    if not app.redis.exists(stream):
        # stream does not exist
        logging.debug(f"Stream {stream:r} does not exist")
        abort(404, "Stream does not exist")
    while 1:
        # check if there are any new entries in the stream
        entries: StreamOutputT = app.redis.xread(  # type: ignore[assignment]
            {stream: entry_id}
        )
        if entries:
            # there are new entries in the stream
            logging.debug("New entries in stream")
            _, data = entries[0]
            for entry_id, entry in data:
                yield entry[b"token"]  # type: ignore[misc]
        if app.redis.get(f"{stream}:status") in ("COMPLETED", b"COMPLETED"):
            # task is complete, stop streaming
            logging.debug("Task is complete")
            # clear the stream
            clear_stream(stream)
            break
        sleep(0.1)


@app.get("stream/<uuid:chat_id>")
@api_output(
    {},
    content_type="text/html",
    status_code=200,
    description="A streamed response",
)
@app.doc(description=docs.CHAT_READ_STREAM)
# @auth_required()
def read_stream(chat_id: UUID):
    """Read a streamed response bit by bit.

    Args:
        chat_id (UUID): the chat to stream
    Yields:
        str | bytes: a token from the AI
    """
    from flask import Response

    from cookgpt.ext import db
    from cookgpt.globals import current_app as app

    logging.info("GET stream for chat %s", chat_id)

    chat = db.session.get(Chat, chat_id)
    if not chat:
        abort(404, "Chat does not exist.")

    user = chat.thread.user
    stream = get_stream_name(user, chat)
    if chat.content:
        # chat has already been streamed
        logging.debug("Chat has already been streamed")
        return Response(stream_with_context(stream_existing_chat(chat)), 200)
    if app.redis.exists(stream):
        # chat is currently being streamed
        logging.debug("Chat is currently being streamed")
        return Response(stream_with_context(stream_from_redis(stream)), 200)
    logging.warning("Chat is not being streamed")
    abort(400, "Chat is not being streamed")


app.add_url_rule(
    "/<uuid:chat_id>",
    view_func=ChatView.as_view("single_chat"),
    methods=["GET", "DELETE"],
)
app.add_url_rule("/all", view_func=ChatsView.as_view("all_chats"))
app.add_url_rule("/", view_func=ChatView.as_view("query"), methods=["POST"])
