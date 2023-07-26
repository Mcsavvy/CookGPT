from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.scoping import scoped_session


class Database(SQLAlchemy):
    """Database"""

    session: "scoped_session"

    def create_all(self, *args, **kwargs):
        """Creates all"""
        from cookgpt.auth.models import JwtToken  # noqa: F401
        from cookgpt.user.models import User  # noqa: F401

        super().create_all(*args, **kwargs)

    def drop_all(self, *args, **kwargs):
        """Drops all"""
        from cookgpt.auth.models import JwtToken  # noqa: F401
        from cookgpt.user.models import User  # noqa: F401

        super().drop_all(*args, **kwargs)


db = Database()
migrate = Migrate()


def init_app(app):
    db.init_app(app)
    migrate.init_app(app, db)
