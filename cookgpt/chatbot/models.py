"""Chatbot models."""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Sequence, cast
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from cookgpt import logging
from cookgpt.ext import cache, db
from cookgpt.ext.cache import (
    chat_cache_key,
    chats_cache_key,
    thread_cache_key,
    threads_cache_key,
)
from cookgpt.utils import utcnow

from .data.enums import MediaType, MessageType

if TYPE_CHECKING:
    from cookgpt.auth.models.user import User  # noqa: F401


class ChatMedia(db.Model):  # type: ignore
    """A media file"""

    serialize_rules = ("-chat", "-secret")

    secret: Mapped[str] = mapped_column(String(36))
    url: Mapped[UUID] = mapped_column(unique=True)
    type: Mapped[MediaType] = mapped_column(Enum(MediaType))
    chat_id: Mapped[UUID] = mapped_column(db.ForeignKey("chat.id"))
    chat: Mapped["Chat"] = db.relationship(  # type: ignore[assignment]
        back_populates="media",
        lazy=True,
        single_parent=True,
        foreign_keys=[chat_id],
    )


class Chat(db.Model):  # type: ignore
    """A single chat in a thread"""

    serialize_rules = "-thread"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    content: Mapped[str] = mapped_column(Text)
    cost: Mapped[int] = mapped_column(default=0)
    chat_type: Mapped[MessageType] = mapped_column(Enum(MessageType))
    thread_id: Mapped[UUID] = mapped_column(db.ForeignKey("thread.id"))
    previous_chat_id: Mapped[Optional[UUID]] = mapped_column(
        db.ForeignKey("chat.id")
    )
    previous_chat: Mapped[
        Optional["Chat"]
    ] = db.relationship(  # type: ignore[assignment]
        remote_side=[id],
        backref=db.backref("next_chat", uselist=False, cascade="all, delete"),
        uselist=False,
        single_parent=True,
        foreign_keys=[previous_chat_id],
    )
    sent_time: Mapped[datetime] = mapped_column(default=utcnow)
    order: Mapped[int] = mapped_column(default=0)
    thread: Mapped["Thread"] = db.relationship(  # type: ignore[assignment]
        back_populates="chats",
        lazy=True,
        single_parent=True,
        foreign_keys=[thread_id],
    )
    media: Mapped[
        List["ChatMedia"]
    ] = db.relationship(  # type: ignore[assignment]
        back_populates="chat",
        lazy=True,
        cascade="all, delete-orphan",
    )

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

    @classmethod
    def create(self, commit=True, **attrs):
        """Create the chat"""
        chat = super().create(commit, **attrs)
        if commit:
            cache.delete(chats_cache_key(thread_id=chat.thread.pk))
            cache.delete(thread_cache_key(thread_id=chat.thread.pk))
            cache.delete(threads_cache_key(user_id=chat.thread.user.pk))
        return chat

    def update(self, commit=True, **attrs):
        """Update the chat"""
        super().update(commit, **attrs)
        if commit:
            cache.delete(chat_cache_key(chat_id=self.pk))
            cache.delete(chats_cache_key(thread_id=self.thread.pk))
        return self

    def delete(self, commit=True):
        """Delete the chat"""
        super().delete(commit)
        if commit:
            cache.delete(chat_cache_key(chat_id=self.pk))
            cache.delete(chats_cache_key(thread_id=self.thread.pk))
            cache.delete(thread_cache_key(thread_id=self.thread.pk))
            cache.delete(threads_cache_key(user_id=self.thread.user.pk))
            # Delete the previous chat's cache
            if self.previous_chat:  # pragma: no cover
                cache.delete(chat_cache_key(chat_id=self.previous_chat.pk))


class Thread(db.Model):  # type: ignore
    """A conversation thread"""

    serialize_rules = ("-user",)

    title: Mapped[str] = mapped_column(db.String(80))
    chats: Mapped[List["Chat"]] = db.relationship(  # type: ignore[assignment]
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="Chat.order",
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = db.relationship(  # type: ignore[assignment]
        back_populates="threads",
        lazy=True,
        single_parent=True,
        foreign_keys=[user_id],
    )
    closed: Mapped[bool] = mapped_column(default=False)

    def __repr__(self):
        num_chats = len(self.chats)  # type: ignore
        return "Thread[{}](user={}, chats={}, closed={})".format(
            self.id.hex[:6],
            self.user.name,
            num_chats,
            "✔" if self.closed else "✗",
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

    @classmethod
    def create(self, commit=True, **attrs):
        """Create the thread"""
        thread = super().create(commit, **attrs)
        if commit:
            cache.delete(threads_cache_key(user_id=thread.user.pk))
        return thread

    def update(self, commit=True, **attrs):
        """Update the thread"""
        thread = super().update(commit, **attrs)
        if commit:
            cache.delete(thread_cache_key(thread_id=self.pk))
            cache.delete(threads_cache_key(user_id=self.user.pk))
        return thread

    def delete(self, commit=True):
        """Delete the thread"""
        super().delete(commit)
        if commit:
            cache.delete(thread_cache_key(thread_id=self.pk))
            cache.delete(threads_cache_key(user_id=self.user.pk))


class ThreadMixin:
    """Mixin class for handling threads"""

    id: "UUID"

    @property
    def total_chat_cost(self):
        """total cost of all messages"""
        return sum(trd.cost for trd in self.threads)  # type: ignore

    def create_thread(self, title: str, closed=False, commit=True):
        """Create a new thread"""
        logging.debug(
            "creating thread: %r for %s %s",
            title,
            self.type.value,  # type: ignore
            self.name,  # type: ignore
        )
        return Thread.create(
            title=title,
            user=self,
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
            try:
                thread = Thread.query.get(thread_id)
            except Thread.DoesNotExist:
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
            self.type.value,  # type: ignore
            self.name,  # type: ignore
        )
        for thread in threads:
            thread.clear()

    def get_active_threads(self) -> Sequence[Thread]:
        """Get all active threads"""
        return Thread.query.filter(
            Thread.user_id == self.id, Thread.closed == False  # noqa: E712
        ).all()
