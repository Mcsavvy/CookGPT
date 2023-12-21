"""Chatbot data validation enums."""
from enum import Enum


class MessageType(Enum):
    """Message type enum."""

    QUERY = "query"
    RESPONSE = "response"


class MediaType(Enum):
    """Different types of media."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
