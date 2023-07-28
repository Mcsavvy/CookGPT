from os import getenv

from apiflask import APIFlask


def configure_secret_key(app: "APIFlask"):
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY not set.")
    env = app.config.current_env.lower()  # type: ignore
    if env == "production":
        if not getenv("APP_SECRET_KEY"):
            raise RuntimeError("APP_SECRET_KEY not set.")
        app.config["SECRET_KEY"] = getenv("APP_SECRET_KEY")


def configure_db_uri(app: "APIFlask"):
    if not app.config["SQLALCHEMY_DATABASE_URI"]:
        raise RuntimeError("SQLALCHEMY_DATABASE_URI not set.")
    env = app.config.current_env.lower()  # type: ignore
    if env == "production":
        if not getenv("APP_DATABASE_URL"):
            raise RuntimeError("APP_DATABASE_URL not set.")
        app.config["SQLALCHEMY_DATABASE_URI"] = getenv("APP_DATABASE_URL")


def init_app(app):
    # configure app
    for config in [configure_secret_key, configure_db_uri]:
        config(app)
