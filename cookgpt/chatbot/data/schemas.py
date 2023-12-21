"""Chatbot data validation schemas."""
from typing import TYPE_CHECKING, Any

from apiflask import Schema, fields
from apiflask.validators import FileSize, FileType
from marshmallow import ValidationError, validates_schema

from cookgpt.chatbot.data.enums import MediaType
from cookgpt.utils import make_field

from . import examples as ex
from .enums import MessageType

if TYPE_CHECKING:
    from cookgpt.chatbot.models import Chat as ChatModel

ChatType = make_field(
    fields.Enum, "chat type", MessageType.QUERY.value, enum=MessageType
)
ChatImage = make_field(
    fields.File,
    "chat image",
    validate=[
        FileType([".png", ".jpg", ".jpeg", ".gif"]),
        FileSize(min="1KB", max="8MB"),
    ],
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


def parse_chat(chat: "ChatModel") -> dict[str, Any]:
    """convert message to dict"""
    return {
        "id": chat.id,
        "content": chat.content,
        "chat_type": chat.chat_type,
        "cost": chat.cost,
        "previous_chat_id": chat.previous_chat_id,
        "next_chat_id": chat.next_chat_id,
        "sent_time": chat.sent_time,
        "thread_id": chat.thread_id,
        "media": [
            {
                "type": media.type,
                "url": media.url,
                "description": media.description
            } for media in chat.media
        ],
    }


class ChatMedia(Schema):
    """Chat media schema."""

    type = fields.Enum(
        MediaType,
        metadata={
            "description": "type of media",
            "example": MediaType.IMAGE.value,
        },
    )
    url = fields.URL(
        metadata={
            "description": "url of media",
            "example": "https://example.com/image.png",
        }
    )
    description = fields.String(
        metadata={
            "description": "description of media",
            "example": "A bowl of jollof rice",
        }
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
    media = fields.List(
        fields.Nested(ChatMedia),
        metadata={
            "description": "list of media",
            "example": [],
        },
    )


class ThreadSchema(Schema):
    """Thread Schema"""

    id = ThreadId()
    title = ThreadTitle()
    chat_count = ThreadChatCount()
    cost = ThreadCost()


class Chat:
    """Chat schema."""

    class Post:
        class Body(Schema):
            image = ChatImage(required=False)
            query = ChatContent(required=False)
            thread_id = ThreadId(
                metadata={
                    "description": (
                        "The id of the thread this chat belongs to. "
                        "If not specified, a new thread will be created."
                    ),
                },
            )

            @validates_schema
            def validate_query(self, data, **kwargs):
                """validate query"""
                if not data.get("image") and not data.get("query"):
                    raise ValidationError("query or image is required")

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

    class MaximumChatCost(Schema):
        """Maximum cost reached error."""

        message = ErrorMessage(
            metadata={
                "example": "maximum cost reached",
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
