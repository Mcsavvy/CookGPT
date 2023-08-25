import click
from flask.cli import with_appcontext
from flask_migrate import Migrate
from flask_migrate.cli import db as db_cli_group
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.scoping import scoped_session


class Database(SQLAlchemy):
    """Database"""

    session: "scoped_session"

    def create_all(self, *args, **kwargs):
        """Creates all"""
        from cookgpt.auth.models import Token, User  # noqa: F401
        from cookgpt.chatbot.models import Chat, Thread  # noqa: F401

        super().create_all(*args, **kwargs)

    def drop_all(self, *args, **kwargs):
        """Drops all"""
        from cookgpt.auth.models import Token, User  # noqa: F401
        from cookgpt.chatbot.models import Chat, Thread  # noqa: F401

        super().drop_all(*args, **kwargs)


db = Database()
migrate = Migrate()


@db_cli_group.command()
@click.option("-d", "drop", is_flag=True, help="Drop all tables in database")
@with_appcontext
def initdb(drop):
    """Initialize database"""
    if drop:
        click.echo("Dropping database...")
        db.drop_all()
    click.echo("Creating database...")
    db.create_all()


@db_cli_group.command()
@with_appcontext
def dropall():
    """drop all tables in database"""
    click.echo("Dropping database...")
    db.drop_all()


def init_app(app):
    db.init_app(app)
    migrate.init_app(app, db)
