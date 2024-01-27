"""Utilities for cookgpt."""
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, NoReturn, ParamSpec, TypeVar

from apiflask import HTTPError
from apiflask.types import SchemaType
from flask import jsonify as flask_jsonify
from flask import make_response


def jsonify(data, status=200):
    """Convert the given data into a JSON response.

    Args:
        data: The data to be converted to JSON.
        status: The HTTP status code (default is 200).

    Returns:
        A JSON response containing the converted data.

    """
    return make_response(flask_jsonify(data), status)


def abort(status_code: int, message: str) -> NoReturn:
    """Raise an HTTPError with the given status code and message.

    Args:
        status_code: The HTTP status code.
        message: The error message.
    """
    raise HTTPError(status_code, message)


def no_ms(dt: datetime) -> datetime:
    """Return datetime without ms."""
    return dt.replace(microsecond=0)


def utcnow() -> datetime:
    """Return utcnow without ms."""
    return no_ms(datetime.now(tz=timezone.utc))


def utcnow_from__ts(timestamp) -> datetime:
    """Return datetime from timestamp without ms."""
    return no_ms(datetime.fromtimestamp(timestamp, tz=timezone.utc))


def api_output(
    schema: SchemaType,
    status_code: int,
    description: str,
    example: Any | None = None,
    examples: dict[str, Any] | None = None,
    links: dict[str, Any] | None = None,
    content_type: str = "application/json",
):
    """Add an API output to the decorated function.

    Args:
        schema: The schema of the output.
        status_code: The HTTP status code.
        description: The description of the output.
        example: An example of the output.
        examples: Examples of the output.
        links: Links of the output.
        content_type: The content type of the output.

    Returns:
        The decorated function.
    """
    from apiflask.openapi import add_response

    if isinstance(schema, type):
        schema = schema()

    def decorator(func):  # pragma: no cover
        if not hasattr(func, "_spec"):
            func._spec = {}
        if func._spec.get("responses", None) is None:
            func._spec["responses"] = {}
        add_response(
            func._spec,
            schema=schema,
            status_code=str(status_code),
            description=description,
            example=example,
            examples=examples,
            links=links,
            content_type=content_type,
        )
        return func

    return decorator


P = ParamSpec("P")
R = TypeVar("R")


def make_field(
    field: Callable[P, R],
    description: str | None = None,
    example: Any | None = None,
    *args,
    **kwargs,
) -> Callable[P, R]:
    """Make a field with default metadata."""
    metadata = {"description": description, "example": example}
    if example is not None:
        metadata["example"] = example
    if description is not None:
        metadata["description"] = description

    def helper(*a: P.args, **k: P.kwargs) -> R:
        metadata.update(k.pop("metadata", {}))  # type: ignore
        k["metadata"] = metadata
        k.update(kwargs)
        a += args  # type: ignore
        return field(*a, **k)

    return helper


def cast_func_to(type: Callable[P, R]):
    """Copy the signature of a function."""

    def cast(func: Callable) -> Callable[P, R]:
        return func  # type: ignore

    return cast
