"""
test user authentication token
"""
from datetime import datetime, timedelta

from cookgpt import config
from cookgpt.models import Token
from cookgpt.utils import utcnow

from .. import random_user
from . import BaseTestCase, update_config


class TestToken(BaseTestCase):
    """test the token model"""

    def test_init(self):
        """test Token.__init__()"""
        user = random_user()
        with self.assertRaises(ValueError) as ctx:
            Token(user=None)
        self.assertEqual(str(ctx.exception), "Token user cannot be empty")

        expiry = timedelta(days=1)
        before = utcnow() + expiry
        with update_config(config, TOKEN_EXPIRY=expiry):
            token = Token(user=user)
        after = utcnow() + expiry

        self.assertEqual(token.user, user, msg="correct user")
        self.assertGreaterEqual(token.expiry, before, msg="correct expiry")
        self.assertLessEqual(token.expiry, after, msg="correct expiry")
        self.assertIsInstance(token.value, str, msg="token is a string")
        self.assertEqual(
            token.value.count("."), 2, msg="token has all 3 parts"
        )

        # decode the token
        decoded = token.decode()
        self.assertEqual(decoded["user"], user.get_id(), msg="correct user")
        self.assertGreaterEqual(
            datetime.fromtimestamp(decoded["exp"]),
            before,
            msg="correct expiry",
        )
        self.assertLessEqual(
            datetime.utcfromtimestamp(decoded["exp"]),
            after,
            msg="correct expiry",
        )

    def test_create(self):
        """test Token.create()"""
        # user = random_user()
        # before = utcnow() + timedelta(days=1)
        # token = Token.create(user)
        # after = utcnow() + timedelta(days=1)

    def test_refresh(self):
        """test Token.refresh()"""
        user = random_user()
        expiry = timedelta(days=1)
        before = utcnow() + expiry
        with update_config(config, TOKEN_EXPIRY=expiry):
            token = Token.create(user=user)
        after = utcnow() + expiry

        self.assertGreaterEqual(token.expiry, before, msg="correct expiry")
        self.assertLessEqual(token.expiry, after, msg="correct expiry")

        before = utcnow() + timedelta(days=1)
        with update_config(config, TOKEN_EXPIRY=timedelta(days=1)):
            token.refresh()
        after = utcnow() + timedelta(days=1)

        self.assertGreaterEqual(token.expiry, before, msg="correct expiry")
        self.assertLessEqual(token.expiry, after, msg="correct expiry")

    def test_serialize(self):
        """test Token.serialize()"""
        user = random_user()
        token = Token.create(user)
        json = token.serialize()

        self.assertEqual(json["id"], token.get_id(), msg="correct id")
        self.assertEqual(json["value"], token.value, msg="correct value")
        self.assertEqual(json["user"], user.get_id(), msg="correct user")
        self.assertEqual(
            json["expiry"], token.expiry.isoformat(), msg="correct expiry"
        )
        self.assertEqual(
            json["has_expired"], token.has_expired(), msg="correct has_expired"
        )
        self.assertEqual(
            json["is_valid"], token.is_valid, msg="correct is_valid"
        )
