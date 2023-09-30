import logging
from logging import Logger, _nameToLevel
from logging.config import dictConfig

from cookgpt.ext.config import config

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
    """get logger"""
    return logging.getLogger("cookgpt")


def log(level: str, msg: str, *args, **kwargs):
    """log"""
    lvl = _nameToLevel[level.upper()]
    get_logger().log(lvl, msg, *args, **kwargs)


def debug(msg: str, *args, **kwargs):
    """debug"""
    get_logger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """info"""
    get_logger().info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """warning"""
    get_logger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """error"""
    get_logger().error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """critical"""
    get_logger().critical(msg, *args, **kwargs)


def exception(msg, *args, exc_info=True, **kwargs):
    """exception"""
    get_logger().exception(msg, *args, exc_info=exc_info, **kwargs)
