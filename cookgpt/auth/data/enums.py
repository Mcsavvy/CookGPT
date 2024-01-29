"""Enums for auth module."""

from enum import Enum


class UserType(Enum):
    """different user types."""

    ADMIN = "admin"
    COOK = "cook"
