"""Chatbot data validation schemas."""
from apiflask import Schema, fields

from cookgpt.utils import make_field

from . import examples as ex
from .enums import MessageType

ChatType = make_field(
    fields.Enum, "chat type", MessageType.QUERY.value, enum=MessageType
)
Content = make_field(fields.String, "chat content", ex.Query)
Cost = make_field(fields.Integer, "chat cost", 100)
PrevChatId = make_field(fields.UUID, "previous chat id", ex.Uuid)
ChatId = make_field(fields.UUID, "chat id", ex.Uuid)
NextChatId = make_field(fields.UUID, "next chat id", ex.Uuid)
SentTime = make_field(fields.DateTime, "time message was sent", ex.DateTime)
ThreadId = make_field(fields.UUID, "chat's thread id", ex.Uuid)
ErrorMessage = make_field(fields.String, "error message", "...")
SuccessMessage = make_field(fields.String, "success message", "...")


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
