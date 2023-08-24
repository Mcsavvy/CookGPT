import os
from datetime import timedelta

import pytest
from dynaconf import Dynaconf

from cookgpt.ext.config import (
    db_uri_hook,
    export_to_env_hook,
    langchain_verbosity_hook,
    secret_key_hook,
    timedeltas_hook,
)


@pytest.fixture(scope="function")
def config(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "testing")
    config = Dynaconf(
        ENVVAR_PREFIX="FLASK",
        ENV_SWITCHER="FLASK_ENV",
        LOAD_DOTENV=False,
        ENVIRONMENTS=True,
        SETTINGS_FILES=["settings.toml"],
        SQLALCHEMY_DATABASE_URI="sqlite:///testing.db",
        SECRET_KEY="testing",
    )
    return config


def test_secret_key_hook(config: Dynaconf, monkeypatch):
    """test secret key hook"""
    assert config.SECRET_KEY == "testing"
    secret_key_hook(config)
    del config.SECRET_KEY
    assert not config("SECRET_KEY")
    with pytest.raises(RuntimeError):
        secret_key_hook(config)
    monkeypatch.setenv("APP_SECRET_KEY", "testing")
    assert "APP_SECRET_KEY" in os.environ
    secret_key_hook(config)


def test_db_uri_hook(config: Dynaconf, monkeypatch):
    """test db uri hook"""
    assert config.SQLALCHEMY_DATABASE_URI == "sqlite:///testing.db"
    db_uri_hook(config)
    del config.SQLALCHEMY_DATABASE_URI
    assert not config("SQLALCHEMY_DATABASE_URI")
    with pytest.raises(RuntimeError):
        db_uri_hook(config)
    monkeypatch.setenv("APP_DATABASE_URL", "sqlite:///testing.db")
    assert "APP_DATABASE_URL" in os.environ
    db_uri_hook(config)


def test_timedeltas_hook(config: Dynaconf):
    config.JWT_ACCESS_TOKEN_LEEWAY = {"seconds": 10}
    config.JWT_ACCESS_TOKEN_EXPIRES = 3600
    config.JWT_REFRESH_TOKEN_EXPIRES = {"minutes": 30}
    config.JWT_REFRESH_TOKEN_LEEWAY = 600
    new_conf = timedeltas_hook(config)
    assert new_conf == {
        "JWT_ACCESS_TOKEN_LEEWAY": timedelta(seconds=10),
        "JWT_ACCESS_TOKEN_EXPIRES": timedelta(seconds=3600),
        "JWT_REFRESH_TOKEN_EXPIRES": timedelta(minutes=30),
        "JWT_REFRESH_TOKEN_LEEWAY": timedelta(seconds=600),
    }

    config.JWT_ACCESS_TOKEN_LEEWAY = "invalid"
    with pytest.raises(ValueError) as exc_info:
        timedeltas_hook(config)
    exc_info.match(
        ("JWT_ACCESS_TOKEN_LEEWAY cannot be converted " "to timedelta")
    )


def test_export_to_env_hook(config: Dynaconf):
    config.OPENAI_API_KEY = "myapikey"
    export_to_env_hook(config)
    assert os.environ["OPENAI_API_KEY"] == "myapikey"


def test_langchain_verbosity_hook(config: Dynaconf):
    import langchain

    config.LANGCHAIN_VERBOSE = True
    langchain_verbosity_hook(config)
    assert langchain.verbose is True
