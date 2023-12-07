from __future__ import annotations

from datetime import datetime
from typing import Optional, Type, Union, cast
from uuid import UUID, uuid4

import click
import sentry_sdk
from flask.cli import with_appcontext
from flask_migrate import Migrate
from flask_migrate.cli import db as db_cli_group
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.model import Model
from flask_sqlalchemy.query import Query
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy_serializer import SerializerMixin
from typing_extensions import deprecated

from cookgpt import logging

IDENT = Union[Union[UUID, str], tuple[Union[UUID, str], ...]]


class BaseQuery(Query):
    """Base Query"""

    @property
    def tables(self) -> set[type[BaseModel]]:
        """Get tables"""
        from sqlalchemy.sql.schema import Table

        _tables: set[type[BaseModel]] = set()
        for element in self._raw_columns:
            if isinstance(element, Table):
                table = cast(
                    type[BaseModel],
                    element._annotations["parententity"].class_,
                )
                _tables.add(table)
        return _tables

    @property
    def model(self) -> "Optional[Type[BaseModel]]":
        """Get model class"""
        tables = self.tables
        if len(tables) == 1:
            return tables.pop()
        return None

    def get(self, ident: IDENT) -> "BaseModel":
        """Get a model by id"""

        if isinstance(ident, str):
            ident = UUID(ident)
        rv = super().get(ident)
        if rv is None:
            if model := self.model:
                raise model.DoesNotExist
            sentry_sdk.set_context(
                "query",
                {
                    "type": "GET",
                    "id": str(ident),
                    "tables:": [table.__name__ for table in self.tables],
                },
            )
            sentry_sdk.capture_message("Multiple models used for one query")
            raise BaseModel.DoesNotExist
        return rv


class ModelErrorMixin:
    """Model Errors"""

    class DoesNotExist(Exception):
        """Does not exist"""

    class CreateError(Exception):
        """Error creating"""

    class UpdateError(Exception):
        """Error updating"""

    class DeleteError(Exception):
        """Error deleting"""

    def __init_subclass__(cls) -> None:
        """Initialize subclass"""
        super().__init_subclass__()
        cls.DoesNotExist = type(  # type: ignore[assignment,misc]
            f"{cls.__name__}.DoesNotExist",
            (cls.DoesNotExist,),
            {"__doc__": f"{cls.__name__} does not exist"},
        )
        cls.CreateError = type(  # type: ignore[assignment,misc]
            f"{cls.__name__}.CreateError",
            (cls.CreateError,),
            {"__doc__": f"Error creating {cls.__name__}"},
        )
        cls.UpdateError = type(  # type: ignore[assignment,misc]
            f"{cls.__name__}.UpdateError",
            (cls.UpdateError,),
            {"__doc__": f"Error updating {cls.__name__}"},
        )
        cls.DeleteError = type(  # type: ignore[assignment,misc]
            f"{cls.__name__}.DeleteError",
            (cls.DeleteError,),
            {"__doc__": f"Error deleting {cls.__name__}"},
        )


class BaseModel(ModelErrorMixin, Model, SerializerMixin):
    """Base model"""

    query: "BaseQuery"  # type: ignore[misc]

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"  # pragma: no cover

    @property
    @deprecated("Use .sid instead")
    def pk(self):
        """Returns primary key"""
        return str(self.id)

    @property
    def sid(self):
        """Returns string id"""
        return str(self.id)

    @classmethod
    def create(cls, commit=True, **kwargs):
        """Creates model"""
        logging.debug("Creating %s with attributes: %s", cls.__name__, kwargs)
        instance = cls(**kwargs)
        if commit:
            instance.save()  # pragma: no cover
        return instance

    def update(self, commit=True, **kwargs):
        """Updates model"""
        logging.debug("Updating %s with attributes: %s", self, kwargs)
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        if commit:
            self.save()  # pragma: no cover
        return self

    def save(self):
        """Saves model"""
        logging.debug(f"Saving {self.__class__}...")
        db.session.add(self)
        db.session.commit()

    def delete(self, commit=True):
        """Deletes model"""
        logging.debug(f"Deleting {self}...")
        db.session.delete(self)
        if commit:
            db.session.commit()  # pragma: no cover


class Database(SQLAlchemy):
    """Database"""

    session: "scoped_session"
    Model: Type[BaseModel]

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


db = Database(model_class=BaseModel, query_class=BaseQuery)
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
