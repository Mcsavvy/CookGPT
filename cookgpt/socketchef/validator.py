from functools import wraps
from inspect import signature
from typing import Any, Callable, ParamSpec, Type, TypeVar

from pydantic import BaseModel, create_model

P = ParamSpec("P")
T = TypeVar("T")


def _is_method(handler) -> bool:
    """Check if a handler is a method."""

    sig = signature(handler)
    if len(sig.parameters) == 0:
        return False
    first_param = next(iter(sig.parameters.values()))
    return first_param.name == "self"


def _snake_to_pascal_case(name: str) -> str:
    """Convert snake case to pascel case."""
    return "".join(word.capitalize() for word in name.split("_"))


def _create_model(handler: Callable) -> Type[BaseModel]:
    """Create a model from a handler."""
    fields: dict[str, Any] = {}

    sig = signature(handler)
    name = _snake_to_pascal_case(handler.__name__)

    for param in sig.parameters.values():
        if param.name == "self":
            continue
        annotation = param.annotation
        if annotation is param.empty:
            if param.default is param.empty:
                raise RuntimeError(
                    f"Cannot validate argument {param.name} "
                    "without an annotation."
                )
            else:
                annotation = type(param.default)
        # if param is a varargs, we need to wrap it in a list
        if param.kind == param.VAR_POSITIONAL:
            annotation = tuple[annotation, ...]  # type: ignore
        # if param is a varkw, we need to wrap it in a dict
        elif param.kind == param.VAR_KEYWORD:
            annotation = dict[str, annotation]  # type: ignore
        if param.default is not param.empty:
            fields[param.name] = (annotation, param.default)
        else:
            fields[param.name] = (annotation, ...)
    return create_model(
        name,
        __module__=handler.__module__,
        **fields,
    )


def validate(handler: Callable[P, T]) -> Callable[P, T]:
    """
    Validate args passed to the SocketIO event handler.
    """

    model = _create_model(handler)

    def _validate_args(handler: Callable[P, T], *args, **kwargs) -> T:
        sig = signature(handler)
        bound = sig.bind(*args, **kwargs)
        is_method = _is_method(handler)

        bound.apply_defaults()
        values: dict[str, Any] = {}
        for name, value in bound.arguments.items():
            if is_method and name == "self":
                continue
            values[name] = value
        validated_args = []
        validated_kwargs = {}
        instance = model(**values)
        for name, value in instance:
            for param in sig.parameters.values():
                if param.name == name:
                    if param.kind == param.VAR_POSITIONAL:
                        validated_args.extend(value)
                    elif param.kind == param.VAR_KEYWORD:
                        validated_kwargs.update(value)
                    else:
                        validated_kwargs[name] = value
                    break
        return (
            handler(args[0], *validated_args, **validated_kwargs)
            if is_method
            else handler(*validated_args, **validated_kwargs)
        )

    @wraps(handler)
    def method_wrapper(self, *args: P.args, **kwargs: P.kwargs) -> T:
        return _validate_args(handler, self, *args, **kwargs)

    @wraps(handler)
    def function_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        return _validate_args(handler, *args, **kwargs)

    wrapper = method_wrapper if _is_method(handler) else function_wrapper

    return wrapper  # type: ignore
