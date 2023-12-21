"""Chatbot chat views"""
from typing import TYPE_CHECKING, Any
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


class ChatsView(MethodView):
    """chats endpoints"""

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
    """Chat endpoints"""

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
        location="form_and_files"
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
    def post(self, form_and_files_data: dict, query_data: dict) -> Any:
        """ To be modified"""
        """Send a message to the chatbot.
        
        """
        from cookgpt.chatbot.tasks import send_query
        from cookgpt.chatbot.utils import get_stream_name
        from cookgpt.globals import current_app as app
        from redisflow import celeryapp
 
        input_key = get_memory_input_key()
        query: str = form_and_files_data["query"]
        media = form_and_files_data["media"]

        user: "User" = get_current_user()

        if "thread_id" in form_and_files_data:
            thread = get_thread(form_and_files_data["thread_id"])
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
        uploadImage(r, media) # Upload the file and edit the chat at once It creates an image in the background
        stream = get_stream_name(user, r)
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
    """Read a streamed response bit by bit."""
    from time import sleep

    from flask import Response

    from cookgpt.ext import db
    from cookgpt.globals import current_app as app
    from redisflow import celeryapp

    logging.info("GET stream for chat %s", chat_id)
    OutputT = list[tuple[bytes, list[tuple[bytes, dict[bytes, bytes]]]]]

    chat = db.session.get(Chat, chat_id)
    if not chat:
        abort(404, "Chat does not exist.")
    logging.debug("Using thread %s", chat.thread.id)
    user: "User" = chat.thread.user
    stream = get_stream_name(user, chat)

    if chat.content != "" or not (
        app.redis.exists(stream) and app.redis.exists(f"{stream}:task")
    ):  # chat has been streamed
        logging.debug("Chat has already been streamed")
        entries: list[str] = []
        for word in chat.content.split(" "):
            entries.extend((word, " "))
        # remove trailing space
        if entries:
            entries.pop()

        return Response(iter(entries), status=200)

    def get_stream(entry_id: bytes):
        logging.debug("Streaming %r from %s", stream, entry_id)

        task_id = app.redis.get(f"{stream}:task")

        while True:
            # check if there are any new entries in the stream
            entries: OutputT = app.redis.xread(  # type: ignore
                {stream: entry_id}
            )
            if entries:
                # there are new entries in the stream
                logging.debug("New entries in stream")
                _, data = entries[0]
                for entry_id, entry in data:
                    yield entry[b"token"]
            elif task_id:
                # there are no new entries in the stream, check if task is
                # complete
                logging.debug("No new entries in stream")
                task = celeryapp.AsyncResult(task_id)
                if task.ready():
                    # task is complete, stop streaming
                    logging.debug("Task is complete")
                    break
            else:  # pragma: no cover
                # there are no new entries in the stream and no task
                # running, stop streaming
                logging.debug("No task running")
                break
            sleep(0.1)

    return Response(stream_with_context(get_stream(b"0-0")), status=200)


app.add_url_rule(
    "/<uuid:chat_id>",
    view_func=ChatView.as_view("single_chat"),
    methods=["GET", "DELETE"],
)
app.add_url_rule("/all", view_func=ChatsView.as_view("all_chats"))
app.add_url_rule("/", view_func=ChatView.as_view("query"), methods=["POST"])
