"""Chatbot data validation schemas."""
from apiflask import Schema, fields

from . import examples as ex
from .enums import MessageType


def Content(**k):
    return fields.String(
        metadata={"description": "chat content", "example": ex.Query}, **k
    )


def ChatType(**k):
    return fields.Enum(
        MessageType,
        metadata={
            "description": "chat type",
            "example": MessageType.QUERY.value,
        },
        **k,
    )


def Cost(**k):
    return fields.Integer(
        metadata={"description": "chat cost", "example": 100}, **k
    )


def PrevChatId(**k):
    return fields.UUID(
        metadata={"description": "previous chat id", "example": ex.Uuid}, **k
    )


def ChatId(**k):
    return fields.UUID(
        metadata={"description": "chat id", "example": ex.Uuid}, **k
    )


def NextChatId(**k):
    return fields.UUID(
        metadata={"description": "next chat id", "example": ex.Uuid}, **k
    )


def SentTime(**k):
    return fields.DateTime(
        metadata={
            "description": "time message was sent",
            "example": ex.DateTime,
        },
        **k,
    )


def ThreadId(**k):
    return fields.UUID(
        metadata={"description": "chat's thread id", "example": ex.Uuid}, **k
    )


def ErrorMessage(**k):
    return fields.String(
        metadata={"description": "error message", "example": "chat not found"},
        **k,
    )


class Chat:
    """Chat schema."""

    class Send(Schema):
        query = Content(required=True)
        # TODO: allow users to select thread
        # thread_id = ThreadId(required=False)

        class Params(Schema):
            stream = fields.Boolean(
                load_default=False,
                metadata={
                    "description": "whether to stream the response",
                    "example": True,
                },
            )

    class Out(Schema):
        id = ChatId()
        content = Content()
        chat_type = ChatType()
        cost = Cost()
        streaming = fields.Boolean(
            dump_default=True,
            metadata={
                "description": "indicates if the chatbot is streaming",
                "example": True,
            },
        )
        previous_chat_id = PrevChatId(allow_none=True)
        next_chat_id = NextChatId(allow_none=True)
        sent_time = SentTime()
        thread_id = ThreadId()

    class Get(Out):
        pass

    class Delete(Schema):
        message = fields.String(
            metadata={
                "description": "message",
                "example": "chat deleted",
            },
        )

    class NotFound(Schema):
        message = ErrorMessage()


class Chats:
    """Chats schema."""

    class Out(Schema):
        chats = fields.List(
            fields.Nested(Chat.Out),
            metadata={
                "description": "list of chats",
                "example": [ex.Chat.Out, ex.Chat.Out],
            },
        )

    class Get(Schema):
        chats = fields.List(
            fields.Nested(Chat.Out),
            metadata={
                "description": "list of chats",
                "example": [ex.Chat.Out, ex.Chat.Out],
            },
        )

    class Delete(Schema):
        message = fields.String(
            metadata={
                "description": "success message",
                "example": "all chats deleted",
            },
        )
