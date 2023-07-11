import warnings

import pkg_resources
from apiflask import APIFlask
from dynaconf.contrib.flask_dynaconf import DynaconfConfig, FlaskDynaconf


class App(APIFlask):
    """App class that extends APIFlask and FlaskDynaconf"""

    config: DynaconfConfig

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        FlaskDynaconf(self)

    def _load_blueprints(self, key="BLUEPRINTS"):
        """Load blueprints from settings.toml"""
        blueprints = self.config.get(key)
        if blueprints is None:
            warnings.warn(
                f"Settings is missing {key} to load blueprints",
                RuntimeWarning,
            )
            return

        for object_reference in self.config[key]:
            # add a placeholder `name` to create a valid entry point
            entry_point_spec = f"__name = {object_reference}"
            # parse the entry point specification
            entry_point = pkg_resources.EntryPoint.parse(entry_point_spec)
            # dynamically resolve the entry point
            blueprint = entry_point.resolve()
            # register the blueprint
            self.register_blueprint(blueprint)


def create_app(**config):
    app = App(__name__)
    app.config.load_extensions(
        "EXTENSIONS"
    )  # Load extensions from settings.toml
    app.config.update(config)  # Override with passed config
    app._load_blueprints()  # Load blueprints from settings.toml
    return app


def create_app_wsgi():
    # workaround for Flask issue
    # that doesn't allow **config
    # to be passed to create_app
    # https://github.com/pallets/flask/issues/4170
    app = create_app()
    return app
