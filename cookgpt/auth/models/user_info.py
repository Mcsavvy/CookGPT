from cookgpt.base import BaseModelMixin
from cookgpt.ext.database import db

from ..data.enums import BloodType, GenderType


class UserInfo(BaseModelMixin, db.Model):  # type: ignore
    """A user's details"""

    serialize_rules = ("-user",)

    date_of_birth = db.Column(db.Date, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)
    blood_type = db.Column(db.Enum(BloodType), nullable=True)
    gender = db.Column(db.Enum(GenderType), nullable=True)


class UserInfoMixin:
    """Mixin for adding extra information to a user"""

    info: UserInfo

    def update_info(self, **info):  # pragma: no cover
        """update this user's info"""
        if not self.info:
            self.info = UserInfo.create(user=self)  # type: ignore
        self.info.update(**info)
        return self.info
