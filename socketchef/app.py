from typing import TypedDict, cast

from apiflask import APIBlueprint
from flask import Request as FlaskRequest
from flask import render_template, request
from flask_socketio import SocketIO, emit
from flask_socketio.namespace import Namespace

from cookgpt import logging


class SocketApp(SocketIO):
    """Custom application class."""

    pass


class SocketEvent(TypedDict):
    """Socket event type."""

    message: str
    """the message sent by the client"""
    args: tuple
    """the arguments sent by the client"""


class Request(FlaskRequest):
    """Custom request class."""

    sid: str
    """The session ID of the client connection."""
    namespace: str
    """The namespace of the request."""
    event: SocketEvent
    """The event of the request."""


socketio = SocketApp()
app = APIBlueprint("socketchef", __name__, url_prefix="/socketchef")
request = cast(Request, request)


@socketio.on("connect")
def test_connect(auth):
    print("Client connected")
    print(f"auth: {auth}")
    print(f"{request.event}")
    emit("my_response", {"data": "Connected"})


@app.get("/")
def index():
    return render_template("index.html")


@socketio.on("my_test_1")
def handle_my_test_1(arg1):
    print("received args: " + arg1)


@socketio.on("my_test_2")
def handle_my_test_2(arg1, arg2):
    print("received args: " + arg1 + arg2)


@socketio.on("my_test_3")
def handle_my_test_3(arg1, arg2, arg3):
    print("received args: " + arg1 + arg2 + arg3)


class ChatNamespace(Namespace):
    def on_connect(self, *args):
        print(len(args))
        return
        logging.debug("Client connected")
        logging.debug(f"SID: {request.sid}")
        logging.debug(f"Auth: {auth}")
        logging.debug(f"Args: {request.event}")
        self.emit("my_response", {"data": "Connected"})

    def on_my_event(self, *args):
        print(len(args))
        # emit("my_response", data)


socketio.on_namespace(ChatNamespace("/chat"))
