from typing import Any

from dynaconf import Dynaconf, Validator


def to_timedelta(value: Any):
    from datetime import timedelta

    if isinstance(value, (float, int)):  # pragma: no cover
        value = timedelta(seconds=value)
    elif isinstance(value, dict):  # pragma: no cover
        value = timedelta(**value)
    if not isinstance(value, timedelta):  # pragma: no cover
        raise ValueError(f"Invalid timedelta value: {value}")
    return value


TIMEDELTAS = Validator(
    "JWT_ACCESS_TOKEN_LEEWAY",
    "JWT_ACCESS_TOKEN_EXPIRES",
    "JWT_REFRESH_TOKEN_EXPIRES",
    "JWT_REFRESH_TOKEN_LEEWAY",
    must_exist=True,
    cast=to_timedelta,
)

APP_ESSENTIALS = Validator(
    "SECRET_KEY",
    "SQLALCHEMY_DATABASE_URI",
    must_exist=True,
)


def export_to_env(config: Dynaconf):
    """export specific config vars to the environment"""
    import os

    if "OPENAI_API_KEY" in config:
        os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY


def set_langchain_verbosity(config: Dynaconf):
    """configure langchain verbosity"""
    import langchain

    langchain.verbose = config.LANGCHAIN_VERBOSE


class Settings(Dynaconf):
    """Custom Dynaconf settings class"""

    def reload(self, env=None, silent=True):
        """reload setings and run validators"""
        self._wrapped.reload(env=env, silent=silent)
        self.validators.validate(
            only=self._validate_only,
            exclude=self._validate_exclude,
            only_current_env=self._validate_only_current_env,
        )

    def setenv(self, env=None, clean=True, silent=True, filename=None):
        """set new environment and run validators"""
        self._wrapped.setenv(
            env=env, clean=clean, silent=silent, filename=filename
        )
        self.validators.validate(
            only=self._validate_only,
            exclude=self._validate_exclude,
            only_current_env=self._validate_only_current_env,
        )

    def init_app(self, app):
        """initialize the app"""
        self.validators.validate()


config = Settings(
    ENVVAR_PREFIX="FLASK",
    ENV_SWITCHER="FLASK_ENV",
    LOAD_DOTENV=False,
    ENVIRONMENTS=True,
    SETTINGS_FILES=["settings.toml", ".secrets.toml"],
    post_hooks=[export_to_env, set_langchain_verbosity],
)

config.validators.register(TIMEDELTAS)
config.validators.register(APP_ESSENTIALS)


init_app = config.init_app
