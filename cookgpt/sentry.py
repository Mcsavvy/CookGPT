"""
Monitoring and Error Tracking Using Sentry.
"""

from logging import ERROR, INFO
from socket import gethostname
from typing import TYPE_CHECKING

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration, ignore_logger
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from cookgpt import logging as logger

if TYPE_CHECKING:
    from cookgpt.ext.config import Dynaconf


def get_centry_integration(config: "Dynaconf"):
    """Get Sentry integrations"""
    flask = FlaskIntegration(
        transaction_style=config.get("SENTRY_TRANSACTION_STYLE", "url")
    )
    sqlalchemy = SqlalchemyIntegration()
    redis = RedisIntegration(
        max_data_size=config.get("SENTRY_REDIS_MAX_DATA_SIZE", 1024)
    )
    celery = CeleryIntegration(
        monitor_beat_tasks=config.get("SENTRY_MONITOR_BEAT_TASKS", False),
        propagate_traces=config.get("SENTRY_PROPAGATE_TRACES", True),
        exclude_beat_tasks=config.get("SENTRY_EXCLUDE_BEAT_TASKS", []),
    )
    logging = LoggingIntegration(
        level=config.get("SENTRY_LOGGING_LEVEL", INFO),
        event_level=config.get("SENTRY_EVENT_LEVEL", ERROR),
    )
    for _logger in config.SENTRY_IGNORED_LOGGERS:
        ignore_logger(_logger)
    integrations = []
    for integration in config.SENTRY_INTEGRATIONS:
        integration = integration.lower()
        try:
            integrations.append(locals()[integration])
            logger.debug(f"Enabled Sentry integration: {integration}")
        except KeyError:  # pragma: no cover
            logger.warning(f"Invalid Sentry integration: {integration}")
    return integrations


def setup(config: "Dynaconf"):
    """Initialize Sentry"""
    from cookgpt.app import VERSION

    if not config.get("SENTRY_DSN"):  # pragma: no cover
        logger.warning("SENTY_DSN is not set. Sentry is disabled.")
        return
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        integrations=get_centry_integration(config),
        traces_sample_rate=config.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=config.SENTRY_PROFILES_SAMPLE_RATE,
        environment=config.current_env,
        release=f"{config.APP_NAME}@{VERSION}",
        debug=config.get("SENTRY_DEBUG", config.DEBUG),
        max_breadcrumbs=config.SENTRY_MAX_BREADCRUMBS,
        attach_stacktrace=config.SENTRY_ATTACH_STACKTRACE,
        include_source_context=config.SENTRY_INCLUDE_SOURCE_CONTEXT,
        send_default_pii=config.SENTRY_SEND_DEFAULT_PII,
        include_local_variables=config.SENTRY_INCLUDE_LOCAL_VARIABLES,
        server_name=gethostname(),
        enable_tracing=config.SENTRY_ENABLE_TRACING,
    )
    logger.info("Sentry initialized.")
