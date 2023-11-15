"""Chat Thread views"""
from typing import TYPE_CHECKING
from uuid import UUID

from apiflask.views import MethodView
from flask_jwt_extended import get_current_user

from cookgpt import logging
from cookgpt.chatbot import app
from cookgpt.chatbot.data import examples as ex
from cookgpt.chatbot.data import schemas as sc
from cookgpt.chatbot.models import Thread
from cookgpt.chatbot.utils import get_thread
from cookgpt.ext.auth import auth_required
from cookgpt.ext.cache import thread_cache_key  # noqa
from cookgpt.ext.cache import cache, threads_cache_key

if TYPE_CHECKING:
    from cookgpt.auth.models.user import User


class ThreadView(MethodView):
    """Thread endpoints"""

    decorators = [auth_required(), app.doc(tags=["thread"])]

    @app.output(sc.Thread.Get.Response)
    @cache.cached(timeout=0, make_cache_key=thread_cache_key)
    def get(self, thread_id: UUID):
        """Get details of a thread."""
        logging.info(f"GET thread using id {thread_id}")
        thread = get_thread(thread_id)
        return sc.Thread.Get.Response().dump(thread)

    @app.input(sc.Thread.Post.Body, example=ex.Thread.Post.Body)
    @app.output(sc.Thread.Post.Response, 201, example=ex.Thread.Post.Response)
    def post(self, json_data: dict):
        """Create a new thread.
        
        You can optionally supply the title of the thread to create by \
        supplying the `title` field in the body of the request
        """
        title = json_data.get("title", "New Thread")
        user: "User" = get_current_user()
        logging.info(f"POST thread {title!r} by {user.name!r}")
        thread = user.create_thread(title=title)
        return {
            "message": "Thread created successfully",
            "thread": thread,
        }, 201

    @app.input(sc.Thread.Patch.Body, example=ex.Thread.Patch.Body)
    @app.output(sc.Thread.Patch.Response, example=ex.Thread.Patch.Response)
    def patch(self, thread_id: UUID, json_data: dict):
        """Modify a thread's information"""
        title = json_data.get("title")
        logging.info(f"PATCH thread {title!r}")
        thread = get_thread(thread_id)
        if title:
            logging.debug(f"Updating thread title to {title!r}")
            thread.update(title=title)
        else:  # pragma: no cover
            logging.debug("No updates to thread")
        return {"message": "Thread updated successfully", "thread": thread}

    @app.output(sc.Thread.Delete.Response, example=ex.Thread.Delete.Response)
    def delete(self, thread_id: UUID):
        """Delete a thread and all chats within it"""
        logging.info(f"DELETE thread {thread_id!r}")
        thread = get_thread(thread_id)
        thread.delete()
        return {"message": "Thread deleted successfully"}


class ThreadsView(MethodView):
    """Threads endpoint"""

    decorators = [auth_required(), app.doc(tags=["thread"])]

    @app.output(sc.Threads.Get.Response, example=ex.Threads.Get.Response)
    @cache.cached(timeout=0, make_cache_key=threads_cache_key)
    def get(self) -> dict:
        """Get all threads"""
        user: "User" = get_current_user()
        logging.info("GET all threads")
        return sc.Threads.Get.Response().dump(
            {"threads": user.get_active_threads()}
        )

    @app.output(sc.Threads.Delete.Response)
    def delete(self):
        """Delete all threads"""
        logging.info("DELETE all threads")
        all_threads = list(
            Thread.query.filter(Thread.closed.__eq__(False)).all()
        )
        for thread in all_threads:
            thread.delete()
        if len(all_threads) == 1:  # pragma: no cover
            substr = "1 thread"
        else:  # pragma: no cover
            substr = f"{len(all_threads)} threads"
        return {"message": f"{substr} deleted successfully"}


app.add_url_rule(
    "/thread", view_func=ThreadView.as_view("create_thread"), methods=["POST"]
)
app.add_url_rule(
    "/thread/<uuid:thread_id>",
    view_func=ThreadView.as_view("single_thread"),
    methods=["GET", "PATCH", "DELETE"],
)
app.add_url_rule("/threads", view_func=ThreadsView.as_view("all_threads"))
