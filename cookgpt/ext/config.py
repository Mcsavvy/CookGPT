from dynaconf import Dynaconf


def secret_key_hook(config: Dynaconf):
    """configure application secret key"""
    if not config("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY not set.")


def db_uri_hook(config: Dynaconf):
    """configure database url"""
    if not config("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("SQLALCHEMY_DATABASE_URI not set.")


def timedeltas_hook(config: Dynaconf):
    """convert config vars into timedeltas"""
    from datetime import timedelta

    TIMEDELTAS = [
        "JWT_ACCESS_TOKEN_LEEWAY",
        "JWT_ACCESS_TOKEN_EXPIRES",
        "JWT_REFRESH_TOKEN_EXPIRES",
        "JWT_REFRESH_TOKEN_LEEWAY",
    ]
    new_conf = {}

    def convert_to_timedelta(key: str):
        val = config.get(key)
        if isinstance(val, dict):
            new_conf[key] = timedelta(**val)
        elif isinstance(val, (float, int)):
            new_conf[key] = timedelta(seconds=val)
        elif isinstance(val, timedelta):  # pragma: no cover
            new_conf[key] = val
        if key not in new_conf:
            raise ValueError(f"{key} cannot be converted to timedelta")

    for key in TIMEDELTAS:
        convert_to_timedelta(key)

    return new_conf


def export_to_env_hook(config: Dynaconf):
    """export specific config vars to the environment"""
    import os

    if "OPENAI_API_KEY" in config:
        os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY


def langchain_verbosity_hook(config: Dynaconf):
    """configure langchain verbosity"""
    import langchain

    langchain.verbose = config.LANGCHAIN_VERBOSE


config = Dynaconf(
    ENVVAR_PREFIX="FLASK",
    ENV_SWITCHER="FLASK_ENV",
    LOAD_DOTENV=False,
    ENVIRONMENTS=True,
    SETTINGS_FILES=["settings.toml", ".secrets.toml"],
    post_hooks=[
        secret_key_hook,
        timedeltas_hook,
        db_uri_hook,
        export_to_env_hook,
        langchain_verbosity_hook,
    ],
)


def init_app(app):
    pass
