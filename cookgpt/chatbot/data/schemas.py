"""Chatbot data validation schemas."""
from apiflask import Schema, fields

from cookgpt.utils import make_field

from . import examples as ex
from .enums import MessageType

ChatType = make_field(
    fields.Enum, "chat type", MessageType.QUERY.value, enum=MessageType
)
ChatContent = make_field(fields.String, "chat content", ex.Query)
ChatCost = make_field(fields.Integer, "cost of this chat", 100)
PrevChatId = make_field(fields.UUID, "previous chat id", ex.Uuid)
ChatId = make_field(fields.UUID, "chat id", ex.Uuid)
NextChatId = make_field(fields.UUID, "next chat id", ex.Uuid)
ChatSentTime = make_field(
    fields.DateTime, "time message was sent", ex.DateTime
)
ThreadId = make_field(fields.UUID, "chat's thread id", ex.Uuid)
ErrorMessage = make_field(fields.String, "error message", "...")
SuccessMessage = make_field(fields.String, "success message", "...")
ThreadTitle = make_field(
    fields.String, "title of the thread", "Jollof Rice Recipe"
)
ThreadChatCount = make_field(
    fields.Integer, "number of chats in this thread", 2
)
ThreadCost = make_field(
    fields.Integer, "cost of all chats in this thread", 220
)
ThreadIsDefault = make_field(
    fields.Boolean, "indicates if this thread is the default thread", True
)


class ChatSchema(Schema):
    """Chat schema."""

    id = ChatId()
    content = ChatContent()
    chat_type = ChatType()  # type: ignore
    cost = ChatCost()
    previous_chat_id = PrevChatId(allow_none=True)
    next_chat_id = NextChatId(allow_none=True)
    sent_time = ChatSentTime()
    thread_id = ThreadId()


class ThreadSchema(Schema):
    """Thread Schema"""

    id = ThreadId()
    title = ThreadTitle()
    chat_count = ThreadChatCount()
    cost = ThreadCost()
    is_default = ThreadIsDefault(attribute="default")


class Chat:
    """Chat schema."""

    class Post:
        class Body(Schema):
            query = ChatContent(required=True)
            thread_id = ThreadId(
                metadata={
                    "description": (
                        "The id of the thread this chat belongs to. "
                        "If not specified, a new thread will be created."
                    ),
                },
            )

        class QueryParams(Schema):
            stream = fields.Boolean(
                load_default=False,
                metadata={
                    "description": "whether to stream the response",
                    "example": True,
                },
            )

        class Response(Schema):
            chat = fields.Nested(ChatSchema)
            streaming = fields.Boolean(
                dump_default=True,
                metadata={
                    "description": "indicates if the chatbot is streaming",
                    "example": True,
                },
            )

    class Get:
        class Response(ChatSchema):
            ...

    class Delete(Schema):
        class Response(Schema):
            message = SuccessMessage(
                metadata={
                    "example": "chat deleted",
                },
            )

    class NotFound(Schema):
        """Chat not found error."""

        message = ErrorMessage(
            metadata={
                "example": "chat not found",
            }
        )


class Chats:
    """Chats schema."""

    class Get:
        class QueryParams(Schema):
            thread_id = ThreadId(
                metadata={"description": "id of thread to get chats from"},
                required=True,
            )

        class Response(Schema):
            chats = fields.List(
                fields.Nested(ChatSchema),
                metadata={
                    "description": "list of chats",
                    "example": [ex.ChatExample, ex.ChatExample],
                },
            )

    class Delete:
        class Body(Schema):
            thread_id = ThreadId(
                metadata={"description": "id of thread to be cleared"},
                required=True,
            )

        class Response(Schema):
            message = SuccessMessage(
                metadata={
                    "example": "all chats deleted",
                },
            )


class Thread:
    """Threads Schema"""

    class Post:
        class Body(Schema):
            """Data to use in thread creation"""

            title = ThreadTitle(allow_none=True)

        class Response(Schema):
            """Details of the created thread"""

            message = SuccessMessage(
                metadata={
                    "example": "thread created",
                },
            )
            thread = fields.Nested(ThreadSchema)

    class Get:
        class Response(ThreadSchema):
            """Details of the thread"""

    class Delete:
        class Response(Schema):
            message = SuccessMessage(metadata={"example": "thread deleted"})

    class Patch:
        class Body(Schema):
            title = ThreadTitle(
                allow_none=True,
                metadata={"description": "the new name of the thread"},
            )

        class Response(Schema):
            """Details of the thread"""

            message = SuccessMessage(
                metadata={
                    "example": "thread updated",
                },
            )
            thread = fields.Nested(ThreadSchema)

    class NotFound(Schema):
        """Thread not found error."""

        message = ErrorMessage(
            metadata={
                "example": "thread not found",
            }
        )


class Threads:
    """Multiple threads schema"""

    class Get:
        class Response(Schema):
            """All threads of this user"""

            threads = fields.List(
                fields.Nested(ThreadSchema),
                metadata={
                    "description": "all threads",
                    "example": [ex.ThreadExample],
                },
            )

    class Delete:
        """Delete all threads"""

        class Response(Schema):
            message = SuccessMessage(
                metadata={"example": "all threads deleted"}
            )
