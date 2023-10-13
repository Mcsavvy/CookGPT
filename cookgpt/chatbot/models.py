"""Chatbot models."""
from typing import Optional, Sequence, cast
from uuid import UUID, uuid4

from cookgpt import logging
from cookgpt.base import BaseModelMixin
from cookgpt.ext.database import db
from cookgpt.utils import utcnow

from .data.enums import MessageType


class Chat(BaseModelMixin, db.Model):  # type: ignore
    """A single chat in a thread"""

    serialize_rules = "-thread"

    id = db.Column(db.Uuid, primary_key=True, default=uuid4)
    content = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Integer, nullable=False, default=0)
    chat_type = db.Column(db.Enum(MessageType), nullable=False)
    thread_id = db.Column(db.Uuid, db.ForeignKey("thread.id"), nullable=False)
    previous_chat_id = db.Column(
        db.Uuid, db.ForeignKey("chat.id"), nullable=True
    )
    previous_chat = db.relationship(
        "Chat",
        remote_side=[id],
        backref=db.backref("next_chat", uselist=False, cascade="all, delete"),
        uselist=False,
        single_parent=True,
        foreign_keys=[previous_chat_id],
    )
    sent_time = db.Column(db.DateTime, nullable=False, default=utcnow)
    order = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (
        db.UniqueConstraint(
            "thread_id", "order", name="unique_order_per_thread"
        ),
    )

    def __repr__(self):
        return "{}[{}](user={}, cost={}, thread={}, prev={}, next={})".format(
            self.chat_type.value.title(),
            self.id.hex[:6],
            self.thread.user.name,
            self.cost,
            self.thread_id.hex[:6],
            self.previous_chat_id.hex[:6] if self.previous_chat_id else "none",
            self.next_chat_id.hex[:6] if self.next_chat_id else "none",
        )

    @property
    def next_chat_id(self) -> "UUID | None":
        """get the next chat's id"""
        if self.next_chat:
            return self.next_chat.id
        return None


class Thread(BaseModelMixin, db.Model):  # type: ignore
    """A conversation thread"""

    serialize_rules = ("-user",)

    title = db.Column(db.String(80), nullable=False)
    chats = db.relationship(
        "Chat",
        backref=db.backref("thread"),
        cascade="all, delete-orphan",
        order_by="Chat.order",
    )
    user_id = db.Column(db.Uuid, db.ForeignKey("user.id"), nullable=False)
    # last_chat_id = db.Column(db.Uuid, db.ForeignKey("chat.id"))
    closed = db.Column(db.Boolean, nullable=False, default=False)
    default = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        num_chats = len(self.chats)  # type: ignore
        return "Thread[{}](user={}, chats={}, closed={}, default={})".format(
            self.id.hex[:6],
            self.user.name,
            num_chats,
            "✔" if self.closed else "✗",
            "✔" if self.default else "✗",
        )

    @property
    def cost(self) -> int:
        """total cost of all messages"""
        return sum(chat.cost for chat in self.chats)  # type: ignore

    @property
    def chat_count(self) -> int:
        """number of messages in the thread"""
        return len(self.chats)  # type: ignore

    @property
    def last_chat(self) -> "Chat":
        """get the last chat in the thread"""
        return (
            Chat.query.filter(Chat.thread_id == self.id, ~Chat.next_chat.has())
            .order_by(Chat.order.desc())
            .first()
        )  # type: ignore

    def add_chat(
        self,
        content: str,
        chat_type: MessageType,
        cost: int = 0,
        previous_chat: "Chat | None" = None,
        commit=True,
        **attrs,
    ) -> "Chat":
        """Add a chat to the thread"""
        logging.debug(
            "adding %s to thread %s: %s",
            chat_type.value.lower(),
            self.id.hex[:6],
            content[:20],
        )
        previous_chat = previous_chat or self.last_chat
        # TODO: if `previous_chat` already has a `next_chat` then
        #       perform doubly-linked list insertion

        if previous_chat and previous_chat.thread_id != self.id:
            raise ValueError("previous_chat not in same thread")

        order = previous_chat.order + 1 if previous_chat else 0
        new_chat = Chat.create(
            commit,
            content=content,
            chat_type=chat_type,
            cost=cost,
            thread=self,
            previous_chat=previous_chat,
            order=order,
            **attrs,
        )
        db.session.flush([new_chat, self])
        db.session.refresh(self)
        return new_chat

    def add_query(
        self,
        content: str,
        cost: int = 0,
        previous_chat: "Chat | None" = None,
        commit=True,
        **attrs,
    ) -> "Chat":
        """Add a query to the thread"""
        return self.add_chat(
            content, MessageType.QUERY, cost, previous_chat, commit, **attrs
        )

    def add_response(
        self,
        content: str,
        cost: int = 0,
        previous_chat: "Chat | None" = None,
        commit=True,
        **attrs,
    ) -> "Chat":
        """Add a response to the thread"""
        return self.add_chat(
            content, MessageType.RESPONSE, cost, previous_chat, commit, **attrs
        )

    def close(self):
        """Close the thread"""
        logging.debug("closing thread %s", self.id.hex[:6])
        self.update(closed=True)

    def clear(self):
        """Clear all messages in the thread"""
        logging.debug(
            "clearing %d chats from thread %s",
            len(self.chats),
            self.id.hex[:6],
        )
        for chat in Chat.query.filter(
            Chat.thread_id == self.id,
            Chat.previous_chat_id == None,  # noqa: E711
        ).all():
            cast(Chat, chat).delete()


class ThreadMixin:
    """Mixin class for handling threads"""

    @property
    def default_thread(self) -> "Thread":
        """Get the default thread for this object"""

        thread = Thread.query.filter_by(
            default=True, user=self, closed=False
        ).first()
        if thread is None:
            thread = self.create_thread(
                title="Default Thread", default=True, commit=True
            )
        return thread

    @property
    def total_chat_cost(self):
        """total cost of all messages"""
        return sum(trd.cost for trd in self.threads)  # type: ignore

    def create_thread(
        self, title: str, default=False, closed=False, commit=True
    ):
        """Create a new thread"""
        logging.debug(
            "creating thread: %r for %s %s",
            title,
            self.get_type().lower(),  # type: ignore
            self.name,  # type: ignore
        )
        return Thread.create(
            title=title,
            user=self,
            default=default,
            closed=closed,
            commit=commit,
        )

    def add_message(
        self,
        content: str,
        chat_type: MessageType,
        cost: int = 0,
        previous_chat: "Chat | None" = None,
        thread_id: Optional[UUID] = None,
        commit=True,
        **attrs,
    ) -> "Chat":
        """Add a message to the thread"""
        if thread_id is None:
            if previous_chat:
                thread = previous_chat.thread
            else:
                raise RuntimeError("thread_id or previous_chat must be given")
        else:
            thread = db.session.get(Thread, thread_id)
            if thread is None:
                raise ValueError("thread_id is invalid")
            if thread.user != self:
                raise ValueError("thread not owned by user")
        return thread.add_chat(
            content=content,
            chat_type=chat_type,
            cost=cost,
            previous_chat=previous_chat,
            commit=commit,
            **attrs,
        )

    def add_query(
        self,
        content: str,
        cost: int = 0,
        previous_chat: "Chat | None" = None,
        thread_id: Optional[UUID] = None,
        commit=True,
        **attrs,
    ) -> "Chat":
        """Add a query to the thread"""
        return self.add_message(
            content,
            MessageType.QUERY,
            cost,
            previous_chat,
            thread_id,
            commit,
            **attrs,
        )

    def add_response(
        self,
        content: str,
        cost: int = 0,
        previous_chat: "Chat | None" = None,
        thread_id: Optional[UUID] = None,
        commit=True,
        **attrs,
    ) -> "Chat":
        """Add a response to the thread"""
        return self.add_message(
            content,
            MessageType.RESPONSE,
            cost,
            previous_chat,
            thread_id,
            commit,
            **attrs,
        )

    def clear_chats(self, threads: Sequence[Thread]):
        """Clear all messages in specified threads"""
        logging.debug(
            "clearing %d threads for %s %r",
            len(threads),
            self.get_type().lower(),  # type: ignore
            self.name,  # type: ignore
        )
        for thread in threads:
            thread.clear()
