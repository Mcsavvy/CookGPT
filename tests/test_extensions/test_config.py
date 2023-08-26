import os

import pytest
from dynaconf import Dynaconf

from cookgpt.ext.config import export_to_env, set_langchain_verbosity


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


def test_export_to_env_hook(config: Dynaconf):
    config.OPENAI_API_KEY = "myapikey"
    export_to_env(config)
    assert os.environ["OPENAI_API_KEY"] == "myapikey"


def test_langchain_verbosity_hook(config: Dynaconf):
    import langchain

    config.LANGCHAIN_VERBOSE = True
    set_langchain_verbosity(config)
    assert langchain.verbose is True
