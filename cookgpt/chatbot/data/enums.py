"""Chatbot data validation enums."""
from enum import Enum


class MessageType(Enum):
    """Message type enum."""

    QUERY = "query"
    RESPONSE = "response"
