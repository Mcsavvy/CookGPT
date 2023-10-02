from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy_serializer import SerializerMixin

from cookgpt import logging
from cookgpt.ext.database import db


class BaseModelMixin(SerializerMixin):
    """Base model"""

    class CreateError(Exception):
        """Create error"""

    class UpdateError(Exception):
        """Update error"""

    id = db.Column(db.Uuid, primary_key=True, default=uuid4)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now(tz=timezone.utc),
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"  # pragma: no cover

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
