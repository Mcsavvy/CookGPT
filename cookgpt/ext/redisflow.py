"""Redisflow extension."""

from typing import TYPE_CHECKING, cast

from redis import Redis  # type: ignore

from cookgpt.globals import setvar

if TYPE_CHECKING:
    from cookgpt.app import App


def init_app(app: "App"):
    """Initialize celery."""
    from cookgpt import logging
    from redisflow import celeryapp

    if hasattr(app, "redis"):  # pragma: no cover
        logging.debug("Redis already initialized")
        return

    logging.debug("Initializing redis")
    redis = cast(Redis, Redis.from_url(app.config.REDIS_URL))
    app.redis = redis
    celeryapp.init_app(app)
    setvar("redis", redis)
