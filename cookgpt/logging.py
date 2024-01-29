"""Logging module."""

import logging
from logging import Logger, _nameToLevel
from logging.config import dictConfig

from cookgpt.ext.config import config
from cookgpt.utils import cast_func_to

# debug settings
debug_mode = config.get("DEBUG", False)


dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "default": {
                "format": "%(message)s",
            },
            "access": {
                "format": "%(message)s",
            },
        },
        "handlers": {
            "console": {
                "level": config.LOG_LEVEL,
                "class": config.LOG_HANDLER_CLASS,
                "formatter": "default",
                "show_time": config.LOG_SHOW_TIME,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "filename": "error.log",
                "maxBytes": 10000,
                "backupCount": 10,
                "delay": "True",
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "access",
                "filename": "access.log",
                "maxBytes": 10000,
                "backupCount": 10,
                "delay": "True",
            },
        },
        "loggers": {
            "gunicorn.error": {
                "handlers": ["console"]
                if debug_mode
                else ["console", "error_file"],
                "level": "INFO",
                "propagate": False,
            },
            "gunicorn.access": {
                "handlers": ["console"]
                if debug_mode
                else ["console", "access_file"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "level": "DEBUG" if debug_mode else "INFO",
            "handlers": ["console"],
        },
    }
)


def get_logger() -> "Logger":
    """Get logger."""
    return logging.getLogger("cookgpt")


@cast_func_to(logging.log)
def log(level: str, msg: str, *args, **kwargs):
    """Log."""
    lvl = _nameToLevel[level.upper()]
    kwargs.setdefault("stacklevel", 2)
    get_logger().log(lvl, msg, *args, **kwargs)


@cast_func_to(logging.debug)
def debug(msg: str, *args, **kwargs):
    """Debug."""
    kwargs.setdefault("stacklevel", 2)
    get_logger().debug(msg, *args, **kwargs)


@cast_func_to(logging.info)
def info(msg, *args, **kwargs):
    """Info."""
    kwargs.setdefault("stacklevel", 2)
    get_logger().info(msg, *args, **kwargs)


@cast_func_to(logging.warning)
def warning(msg, *args, **kwargs):
    """Warning"""
    kwargs.setdefault("stacklevel", 2)
    get_logger().warning(msg, *args, **kwargs)


@cast_func_to(logging.error)
def error(msg, *args, **kwargs):
    """Error"""
    kwargs.setdefault("stacklevel", 2)
    get_logger().error(msg, *args, **kwargs)


@cast_func_to(logging.critical)
def critical(msg, *args, **kwargs):
    """Critical."""
    kwargs.setdefault("stacklevel", 2)
    get_logger().critical(msg, *args, **kwargs)


@cast_func_to(logging.exception)
def exception(msg, *args, exc_info=True, **kwargs):
    """Exception."""
    kwargs.setdefault("stacklevel", 2)
    get_logger().exception(msg, *args, exc_info=exc_info, **kwargs)
