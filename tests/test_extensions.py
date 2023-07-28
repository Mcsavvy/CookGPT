import os

import pytest

from cookgpt.app import App
from cookgpt.ext.config import configure_secret_key


class TestConfigureSecretKey:
    @pytest.fixture
    def app(self):
        os.environ["FLASK_ENV"] = "testing"
        app = App(__name__)
        app.config["SECRET_KEY"] = "test_secret_key"
        return app

    def test_correct_env(self, app):
        assert app.config["ENV"] == "testing"

    def test_with_secret_key_set(self, app):
        configure_secret_key(app)
        assert app.config["SECRET_KEY"] == "test_secret_key"

    def test_with_secret_key_not_set(self, app):
        app.config["SECRET_KEY"] = None
        with pytest.raises(RuntimeError, match="SECRET_KEY not set."):
            configure_secret_key(app)

    def test_with_env_not_production(self, app, monkeypatch):
        monkeypatch.delenv("APP_SECRET_KEY", raising=False)
        configure_secret_key(app)
        assert app.config["SECRET_KEY"] == "test_secret_key"

    def test_with_env_production_and_app_secret_key_set(
        self, app, monkeypatch
    ):
        monkeypatch.setenv("APP_SECRET_KEY", "test_app_secret_key")
        assert os.getenv("APP_SECRET_KEY") == "test_app_secret_key"
        with app.config.using_env("production"):
            print(f"env: {app.config.current_env}")
            configure_secret_key(app)
            assert app.config["SECRET_KEY"] == "test_app_secret_key"

    def test_with_env_production_and_app_secret_key_not_set(
        self, app, monkeypatch
    ):
        monkeypatch.delenv("APP_SECRET_KEY", raising=False)
        assert "APP_SECRET_KEY" not in os.environ
        with app.config.using_env("production"), pytest.raises(
            RuntimeError, match="APP_SECRET_KEY not set."
        ):
            configure_secret_key(app)
