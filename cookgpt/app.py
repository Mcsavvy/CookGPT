from importlib.metadata import EntryPoint
from pathlib import Path
from socket import gethostname

from apiflask import APIFlask
from dynaconf import Dynaconf, FlaskDynaconf
from redis import Redis  # type: ignore

from cookgpt import logging  # noqa: F401
from cookgpt import docs
from cookgpt.ext.config import config

VERSION = Path(__file__).parent.joinpath("VERSION").read_text().strip()


def schema_name_resolver(schema):  # pragma: no cover
    name = schema.__class__.__qualname__.replace(
        ".", ":"
    )  # get schema class name
    if name.endswith("Schema"):  # remove the "Schema" suffix
        name = name[:-6] or name
    if schema.partial:  # add a "Update" suffix for partial schema
        name += "Update"
    return name


class App(APIFlask):
    """App class that extends APIFlask and FlaskDynaconf"""

    config: "Dynaconf"
    redis: "Redis"

    def __init__(self, *args, **kwargs):
        kwargs.update(
            title="Cookgpt", version=VERSION, docs_ui="elements", docs_path="/"
        )
        super().__init__(*args, **kwargs)

        self.schema_name_resolver = schema_name_resolver
        self.description = docs.APP
        FlaskDynaconf(self, dynaconf_instance=config)

    def __repr__(self) -> str:
        return f"<App '{self.import_name}' env='{self.config.current_env}'>"

    def load_blueprints(self, key="BLUEPRINTS"):
        """Load blueprints from settings.toml"""
        blueprints = self.config.get(key, [])
        for object_reference in blueprints:
            # parse the entry point specification
            logging.debug(f"Loading blueprint: {object_reference}")
            entry_point = EntryPoint(
                name=None, group=None, value=object_reference  # type: ignore
            )
            # dynamically resolve the blueprint
            blueprint = entry_point.load()
            # register the blueprint
            self.register_blueprint(blueprint)


def add_application_info(response):
    """Add application info to response headers"""
    logging.debug("Adding application info to response headers...")
    response.headers["X-HostName"] = gethostname()
    response.headers["X-Application"] = "Cookgpt"
    response.headers["X-Version"] = VERSION
    return response


def create_app(**config):
    import os

    os.environ.setdefault("FLASK_ENV", "PRODUCTION")
    logging.debug(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
    logging.info("Creating app cookgpt...")
    app = App(__name__)
    app.config.update(config)  # Override with passed config
    logging.info("Loading extensions...")
    app.config.load_extensions()  # Load extensions
    logging.info("Loading blueprints...")
    app.load_blueprints()  # Load blueprints
    logging.info("Reloading configurations...")
    app.config._settings.reload()
    app.after_request(add_application_info)
    return app


def create_app_wsgi():  # pragma: no cover
    # workaround for Flask issue
    # that doesn't allow **config
    # to be passed to create_app
    # https://github.com/pallets/flask/issues/4170
    app = create_app()
    return app
