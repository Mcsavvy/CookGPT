from functools import wraps
from importlib.metadata import EntryPoint
from typing import (
    TYPE_CHECKING,
    Callable,
    Optional,
    ParamSpec,
    TypedDict,
    TypeVar,
    cast,
)
from uuid import UUID

import sentry_sdk
from apiflask import APIBlueprint
from flask import Request as FlaskRequest
from flask import render_template
from flask import request as _request
from flask_socketio import SocketIO
from flask_socketio.namespace import Namespace as SocketIONamespace

from cookgpt.auth.models import Token, User
from cookgpt.ext.database import db
from cookgpt.globals import namespace, use_namespace
from cookgpt.utils import cast_func_to

if TYPE_CHECKING:
    from cookgpt.app import App

from cookgpt import logging

P = ParamSpec("P")
T = TypeVar("T")


class SocketApp(SocketIO):
    """Custom application class."""

    webapp: "App"

    def _set_namespaces(self, config):
        """Set namespaces."""
        logging.debug("Setting namespaces...")
        for namespace, handler in config.NAMESPACES.items():  # noqa: F402
            logging.debug(f"Registering namespace '{namespace}'...")
            entry_point = EntryPoint(name=None, group=None, value=handler)
            handler_class = entry_point.load()
            self.on_namespace(handler_class(f"/{namespace}"))

    @cast_func_to(SocketIO.init_app)
    def init_app(self, app: "App", **kwargs):
        """Initialize the application."""
        self._set_namespaces(app.config)
        self.webapp = app
        if app.config.MESSAGE_QUEUE_ENABLED:
            kwargs.setdefault(  # type: ignore
                message_queue=app.config.REDIS_URL
            )
        super().init_app(app, **kwargs)

    @classmethod
    def auth_required(cls, fn: Callable[P, T]) -> Callable[P, T]:
        """Decorator to require authentication."""

        @wraps(fn)
        def wrapper(*args, **kwargs):
            logging.info("Checking authentication...")
            if namespace.active_token is None:
                logging.warning(
                    (
                        f"Client does not have an active session with "
                        f"namespace {cls.namespace}"
                    )
                )
                namespace.disconnect(request.sid)
            user = namespace.active_token.user
            sentry_sdk.set_user(
                {
                    "id": user.pk,
                    "username": user.name,
                    "email": user.email,
                }
            )
            sentry_sdk.set_tag("user.sid", request.sid)
            return fn(*args, **kwargs)

        logging.info("Authentication successful.")
        return wrapper


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


class Namespace(SocketIONamespace):
    """Custom namespace class."""

    socketio: "SocketApp"
    _active_token: Optional["Token"] = None
    _current_user: Optional["User"] = None
    sid: Optional[str] = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.namespace!r})"

    @property
    def active_token(self) -> "Optional[Token]":
        """Get the active token."""
        token_id = self.socketio.webapp.redis.get(
            f"{self.namespace}:{request.sid}:atoken"
        )
        if token_id is None:
            return None
        token_id = UUID(cast(bytes, token_id).decode())
        token = db.session.get(Token, token_id)
        return token

    @active_token.setter
    def active_token(self, token: "Optional[Token]"):
        """Set the active token."""
        if token is None:
            self.socketio.webapp.redis.delete(
                f"{self.namespace}:{request.sid}:atoken"
            )
            return
        self.socketio.webapp.redis.set(
            f"{self.namespace}:{request.sid}:atoken",
            token.id.hex,
        )

    @property
    def current_user(self) -> "Optional[User]":
        """Get the current user."""

        if self.active_token is None:
            return None
        return self.active_token.user

    def on_error(self, err: Exception):
        """Handle errors."""
        logging.error(err)
        self.emit("error", {"error": "An error occurred."})

    def on_connect(self, *args):
        """Handle a connection."""
        from flask_jwt_extended import get_jwt
        from flask_jwt_extended.exceptions import JWTExtendedException
        from flask_jwt_extended.view_decorators import verify_jwt_in_request
        from jwt.exceptions import PyJWTError
        from sentry_sdk import capture_exception
        from socketio.exceptions import ConnectionRefusedError

        if self.current_user is not None:
            logging.info("Client already connected.")
            self.emit("connected", {"message": "Connected."})
            return
        logging.info("Authenticating user...")
        try:
            verify_jwt_in_request(locations=["headers", "query_string"])
            auth_success = True
        except (
            PyJWTError,
            JWTExtendedException,
        ) as err:
            capture_exception(err)
            logging.error(err)
            raise ConnectionRefusedError(*err.args)
        if not auth_success:
            logging.warning("Couldn't authenticate user.")

        token = db.session.get(Token, UUID(get_jwt()["jti"]))
        assert token is not None
        self.active_token = token
        logging.info(
            (
                f"Client connected to {self.namespace} "
                f"as {token.user.name} ({request.sid})"
            )
        )

        self.emit("connected", {"message": "Connected."})

    def on_disconnect(self, *args):
        """Handle a disconnection."""
        logging.info(f"Client disconnected from {self.namespace}")
        self.active_token = None
        sentry_sdk.set_user({"ip_address": "{{auto}}"})

    def trigger_event(self, event: str, *args):
        """Trigger an event."""
        with sentry_sdk.configure_scope() as scope, use_namespace(self):
            sentry_sdk.set_tag("socketio.event", event)
            sentry_sdk.set_tag("socketio.namespace", self.namespace)
            scope.set_transaction_name(f"socket.io:{self.namespace}/{event}")
            try:
                result = super().trigger_event(event, *args)
            except Exception as err:
                sentry_sdk.capture_exception(err)
                logging.error(err, exc_info=True)
                raise
            finally:
                sentry_sdk.set_tag("socketio.event", None)
                sentry_sdk.set_tag("socketio.namespace", None)
        return result

    @classmethod
    def on(cls, event: str):
        """
        Register an event handler in this namespace.

        Args:
            event: The event to handle.
        """

        def decorator(fn: Callable[P, T]) -> Callable[P, T]:
            @wraps(fn)
            def wrapper(self, *args: P.args, **kwargs: P.kwargs):
                return fn(*args, **kwargs)

            setattr(cls, f"on_{event}", wrapper)
            return fn

        return decorator


socketio = SocketApp()
app = APIBlueprint("socketchef", __name__, url_prefix="/socketchef")
request = cast(Request, _request)


@app.get("/")
def index():
    return render_template("index.html")


__all__ = [
    "Namespace",
    "SocketApp",
    "socketio",
    "app",
]
