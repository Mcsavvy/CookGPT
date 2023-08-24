"""Test User's info"""
from datetime import date
from uuid import UUID

from cookgpt.models import BloodType, Gender, UserInfo

from .. import random_user
from . import BaseTestCase


class TestUserInfo(BaseTestCase):
    """test the user info model"""

    def test_init(self):
        """test UserInfo.__init__()"""
        user = random_user()
        with self.assertRaises(ValueError) as ctx:
            UserInfo(user=None)
        self.assertEqual(str(ctx.exception), "user must be provided")
        info = UserInfo(
            user=user,
            date_of_birth="2000-01-01",
            weight="100kg",
            height="6ft2in",
            blood_type="A+",
            gender="male",
        )
        self.assertIsNone(info.id, msg="id not set yet")
        self.assertEqual(info.user, user, msg="correct user")
        self.assertEqual(
            info.date_of_birth, date(2000, 1, 1), msg="correct date of birth"
        )
        self.assertEqual(info.weight, 100, msg="correct weight")
        self.assertGreaterEqual(info.height, 1.87, msg="correct height")
        self.assertLessEqual(info.height, 1.88, msg="correct height")
        self.assertEqual(
            info.blood_type, BloodType.a_positive, msg="correct blood type"
        )
        self.assertEqual(info.gender, Gender.male, msg="correct gender")

    def test_create(self):
        """test UserInfo.create()"""
        user = random_user()
        info = UserInfo.create(
            user=user,
            date_of_birth="2000-01-01",
            weight="100kg",
            height="6ft",
            blood_type="A+",
            gender="male",
        )
        self.assertIsInstance(info.id, UUID, msg="id is set")
        self.assertIs(user.info, info, msg="user info is set")
        self.assertEqual(info.user, user, msg="correct user")
        self.assertEqual(
            info.date_of_birth, date(2000, 1, 1), msg="correct date of birth"
        )
        self.assertEqual(info.weight, 100, msg="correct weight")
        self.assertGreaterEqual(info.height, 1.82, msg="correct height")
        self.assertLessEqual(info.height, 1.83, msg="correct height")
        self.assertEqual(
            info.blood_type, BloodType.a_positive, msg="correct blood type"
        )
        self.assertEqual(info.gender, Gender.male, msg="correct gender")

    def test_serialize(self):
        """test UserInfo.serialize()"""
        user = random_user()
        info = UserInfo.create(
            user=user,
            date_of_birth="2000-01-01",
            weight="100kg",
            height="2.5m",
            blood_type="A+",
            gender="male",
        )
        json = info.serialize()
        self.assertIsInstance(json, dict, msg="serialised to a dict")
        self.assertEqual(json["id"], info.get_id(), msg="correct id")
        self.assertEqual(json["user"], user.get_id(), msg="correct user")
        self.assertEqual(
            json["date_of_birth"], "2000-01-01", msg="correct date of birth"
        )
        self.assertEqual(json["weight"], 100, msg="correct weight")
        self.assertEqual(json["height"], 2.5, msg="correct height")
        self.assertEqual(json["blood_type"], "A+", msg="correct blood type")

    def test_update(self):
        """test UserInfo.update()"""
        user = random_user()
        info = UserInfo.create(user=user)

        info.update(
            date_of_birth="2000-01-01",
            weight="100kg",
            height="1.5",
            blood_type="A+",
            gender="male",
        )
        self.assertEqual(info.user, user, msg="correct user")
        self.assertEqual(
            info.date_of_birth, date(2000, 1, 1), msg="correct date of birth"
        )
        self.assertEqual(info.weight, 100, msg="correct weight")
        self.assertEqual(info.height, 1.50, msg="correct height")
        self.assertEqual(
            info.blood_type, BloodType.a_positive, msg="correct blood type"
        )
        self.assertEqual(info.gender, Gender.male, msg="correct gender")

        # updating only one field should not change the others
        info.update(date_of_birth="2003-01-01")
        self.assertEqual(
            info.date_of_birth, date(2003, 1, 1), msg="correct date of birth"
        )
        self.assertEqual(info.weight, 100, msg="correct weight")
        self.assertEqual(info.height, 1.50, msg="correct height")
        self.assertEqual(
            info.blood_type, BloodType.a_positive, msg="correct blood type"
        )
        self.assertEqual(info.gender, Gender.male, msg="correct gender")

        # protected fields cannot be updated
        for attr in ("id", "user", "user_id"):
            with self.assertRaises(UserInfo.UpdateError) as ctx:
                info.update(**{attr: "new value"})
            self.assertEqual(
                str(ctx.exception),
                f"cannot update {attr}",
                msg=f"cannot update {attr}",
            )
