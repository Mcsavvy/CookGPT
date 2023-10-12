"""Chat Thread views"""
from typing import TYPE_CHECKING
from uuid import UUID

from apiflask.views import MethodView

from cookgpt.chatbot import app
from cookgpt.chatbot.data import examples as ex
from cookgpt.chatbot.data import schemas as sc
from cookgpt.ext.auth import auth_required

if TYPE_CHECKING:
    pass


class ThreadView(MethodView):
    """Thread endpoints"""

    decorators = [auth_required(), app.doc(tags=["thread"])]

    @app.output(sc.Thread.Get.Response)
    def get(self, thread_id: UUID):
        """Get details of a thread."""

    @app.input(sc.Thread.Post.Body, example=ex.Thread.Post.Body)
    @app.output(sc.Thread.Post.Response, 201, example=ex.Thread.Post.Response)
    def post(self, json_data: dict):
        """Create a new thread.
        
        You can optionally supply the title of the thread to create by \
        supplying the `title` field in the body of the request
        """

    @app.input(sc.Thread.Patch.Body, example=ex.Thread.Patch.Body)
    @app.output(sc.Thread.Patch.Response, example=ex.Thread.Patch.Response)
    def patch(self, json_data: dict):
        """Modify a thread's information"""

    @app.output(sc.Thread.Delete.Response, example=ex.Thread.Delete.Response)
    def delete(self):
        """Delete a thread and all chats within it"""


class ThreadsView(MethodView):
    """Threads endpoint"""

    decorators = [auth_required(), app.doc(tags=["thread"])]

    @app.output(sc.Threads.Get.Response, example=ex.Threads.Get.Response)
    def get():
        """Get all threads"""

    @app.output(sc.Threads.Delete.Response)
    def delete():
        """Delete all threads"""


app.add_url_rule(
    "/thread", view_func=ThreadView.as_view("create_thread"), methods=["POST"]
)
app.add_url_rule(
    "/thread/<uuid:thread_id>",
    view_func=ThreadView.as_view("single_thread"),
    methods=["GET", "PATCH", "DELETE"],
)
app.add_url_rule("/threads", view_func=ThreadsView.as_view("all_threads"))
