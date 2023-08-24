"""
Test database models
"""
from datetime import datetime, timedelta
from time import sleep
from uuid import UUID

from cookgpt import config
from cookgpt.utils import utcnow

from .. import (random_email, random_first_name, random_last_name,
                random_password, random_user, random_username, random_weight)
from . import BaseTestCase, Message, Token, User, UserInfo, update_config


class TestUser(BaseTestCase):
    """Test user model"""

    def setUp(self) -> None:
        self.config_ctx = update_config(
            config,
            TOKEN_EXPIRY=timedelta(hours=10),
            TOKEN_REISSUANCE_LEEWAY=timedelta(hours=3),
        )
        self.config_ctx.__enter__()
        return super().setUp()

    def tearDown(self) -> None:
        self.config_ctx.__exit__(None, None, None)
        return super().tearDown()

    def test_firstname_lastname(self):
        """test User.first_name and User.last_name"""
        fname1 = random_first_name()
        lname1 = random_last_name()
        user1 = random_user(fname1, lname1)
        self.assertEqual(user1.first_name, fname1, msg="correct first name")
        self.assertEqual(user1.last_name, lname1, msg="correct last name")

        with self.assertRaises(User.CreateError) as ctx:
            random_user(fname1, lname1)
        self.assertEqual(
            ctx.exception.args[0],
            "name is taken",
            msg="firstname and lastname must be unique together",
        )
        user2 = random_user(fname1, random_last_name())  # should not raise

        with self.assertRaises(User.UpdateError) as ctx:
            user1.update(last_name=user2.last_name)
        self.assertEqual(
            ctx.exception.args[0],
            "name is taken",
            msg="firstname and lastname must be unique together",
        )
        user1.update(first_name=fname1, last_name=lname1)  # should not raise

    def test_create(self):
        """test User.create()"""
        user = random_user()
        self.assertIsInstance(user, User, msg="user is an instance of User")
        self.assertIsInstance(user.id, UUID, msg="id has been set")
        self.assertIsNone(user.info, msg="user info not created")
        user.delete()
        user = random_user(weight=random_weight())
        self.assertIsInstance(user.info, UserInfo, msg="user info created")

    def test_verify_password(self):
        """test user.verify_password()"""
        password1 = random_password()
        password2 = random_password()
        user1 = random_user(password=password1)
        user2 = random_user(password=password2)

        self.assertTrue(user1.verify_password(password1))
        self.assertFalse(user1.verify_password("wrongpassword"))
        self.assertTrue(user2.verify_password(password2))
        self.assertFalse(user2.verify_password("wrongpassword"))
        self.assertFalse(user1.verify_password(password2))
        self.assertFalse(user2.verify_password(password1))

    def test_serialize(self):
        """test User.serialize()"""
        fname1 = random_first_name()
        lname1 = random_last_name()
        username1 = random_username()
        email1 = random_email()
        password1 = random_password()
        user1 = random_user(fname1, lname1, email1, password1, username1)
        json = user1.serialize()

        self.assertIn("first_name", json, msg="first_name is exposed")
        self.assertIn("last_name", json, msg="last_name is exposed")
        self.assertIn("username", json, msg="username is exposed")
        self.assertIn("email", json, msg="email is exposed")
        self.assertNotIn("password", json, msg="password should be hidden")
        self.assertIn("messages", json, msg="messages is exposed")
        self.assertIn("info", json, msg="info is exposed")
        self.assertNotIn("tokens", json, msg="tokens should be hidden")

        self.assertEqual(
            json["first_name"], fname1, msg="first_name is correct"
        )
        self.assertEqual(json["last_name"], lname1, msg="last_name is correct")
        self.assertEqual(
            json["username"], username1, msg="username is correct"
        )
        self.assertEqual(json["email"], email1, msg="username is correct")
        self.assertEqual(
            json["messages"], [], msg="messages starts off as an empty list"
        )
        self.assertIsNone(
            json["info"],
            msg="info is None when there none attached the class yet",
        )

        fname2 = random_first_name()
        lname2 = random_last_name()
        username2 = random_username()
        email2 = random_email()
        password2 = random_password()
        user2 = random_user(fname2, lname2, email2, password2, username2)
        for i in range(1, 6):
            user2.add_message(f"query {i}", f"response {i}", cost=i)
        user2.update_info()
        json = user2.serialize()

        self.assertIn("first_name", json, msg="first_name is exposed")
        self.assertIn("last_name", json, msg="last_name is exposed")
        self.assertIn("username", json, msg="username is exposed")
        self.assertIn("email", json, msg="email is exposed")
        self.assertNotIn("password", json, msg="password should be hidden")
        self.assertIn("messages", json, msg="messages is exposed")
        self.assertIn("info", json, msg="info is exposed")
        self.assertNotIn("tokens", json, msg="tokens should be hidden")

        self.assertEqual(
            json["messages"],
            [msg.get_id() for msg in user2.messages],
            msg="messages is a list of the ids of messages attached to a user",
        )
        self.assertEqual(
            json["info"],
            user2.info.get_id(),
            msg="info is the id of the UserInfo attached to the user",
        )

    def test_token_mixin(self):
        """test User.token functionality"""
        reissuance_leeway: timedelta = config["TOKEN_REISSUANCE_LEEWAY"]

        user = random_user()
        self.assertEqual(user.tokens, [], msg="user's tokens starts off empty")
        tk1 = user.new_token()
        tk2 = user.new_token()
        tk3 = user.new_token()

        for tk in (tk1, tk2, tk3):
            self.assertIsInstance(
                tk, Token, msg="an instance of a token is returned"
            )
        self.assertNotEqual(tk1, tk2, msg="each token is unique")
        self.assertNotEqual(tk1, tk3, msg="each token is unique")
        self.assertNotEqual(tk2, tk3, msg="each token is unique")

        self.assertEqual(len(user.tokens), 3, "new tokens were created")
        tk4 = user.request_token()
        self.assertEqual(len(user.tokens), 3, "no new token was created")
        self.assertEqual(tk4, tk3, msg="most recent token is reissued")

        self.assertTrue(user.invalidate_token(tk4), msg="token invalidated")
        tk5 = user.request_token()
        self.assertEqual(len(user.tokens), 3, "no new token was created")
        self.assertEqual(tk5, tk2, msg="most recent valid token is reissued")

        tk5.update(expiry=utcnow() - timedelta(seconds=1))
        tk6 = user.request_token()
        self.assertEqual(len(user.tokens), 3, "no new token was created")
        self.assertEqual(
            tk6, tk1, msg="most recent valid unexpired token is reissued"
        )

        # if the most recent valid key has crossed the reissuance validity
        # period it can no longer be reissued
        tk1.update(expiry=(datetime.utcnow() + reissuance_leeway))
        sleep(1)
        tk7 = user.request_token()
        self.assertEqual(len(user.tokens), 4, "a new token was created")
        self.assertNotIn(
            tk7,
            (tk1, tk2, tk3),
            msg="a new token is issued if no valid unexpired one is found",
        )

        self.assertTrue(user.purge_bad_tokens(), msg="purged bad tokens")
        self.assertEqual(len(user.tokens), 2, msg="tokens deleted")
        self.assertEqual(
            user.tokens,
            [tk1, tk7],
            msg="only invalid and expired token are left",
        )
        # User.get_token()
        self.assertEqual(
            user.get_token(tk1.value), tk1, msg="User.get_token()"
        )
        self.assertEqual(
            user.get_token(tk7.value), tk7, msg="User.get_token()"
        )

        # user.invalidate_token()
        self.assertTrue(user.invalidate_token(tk1), msg="token invalidated")
        self.assertFalse(tk1.is_valid)
        self.assertTrue(
            user.invalidate_token(tk7.value), msg="token invalidated"
        )
        self.assertFalse(tk7.is_valid)
        self.assertFalse(
            user.invalidate_token("not a token"), msg="token not found"
        )

    def test_message_mixin(self):
        """test User.message functionality"""
        # create message
        user = random_user()
        self.assertEqual(
            user.messages, [], msg="user's messages starts off empty"
        )

        now1 = utcnow()
        msg1 = user.add_message("message one")
        now2 = utcnow()
        self.assertIsInstance(
            msg1, Message, msg="create a message w/o response"
        )
        self.assertGreaterEqual(msg1.sent_at, now1, msg="sent_at is accurate")
        self.assertLessEqual(msg1.sent_at, now2, msg="sent_at is accurate")
        self.assertIs(msg1.user, user, msg="correct user")
        self.assertEqual(msg1.content, "message one", msg="message is correct")
        self.assertIsNone(msg1.response, msg="no response yet")
        self.assertIsNone(msg1.responded_at, msg="responded_at not set yet")

        now1 = utcnow()
        msg2 = user.add_message("message two", "response two", cost=20)
        now2 = utcnow()
        self.assertIsInstance(
            msg2, Message, msg="create a message w/o response"
        )
        self.assertGreaterEqual(msg2.sent_at, now1, msg="sent_at is accurate")
        self.assertLessEqual(msg2.sent_at, now2, msg="sent_at is accurate")
        self.assertGreaterEqual(
            msg2.responded_at, now1, msg="sent_at is accurate"
        )
        self.assertLessEqual(
            msg2.responded_at, now2, msg="sent_at is accurate"
        )
        self.assertIs(msg2.user, user, msg="correct user")
        self.assertEqual(msg2.content, "message two", msg="message is correct")
        self.assertEqual(
            msg2.response, "response two", msg="response is correct"
        )

        self.assertEqual(
            user.messages,
            [msg1, msg2],
            msg="messages are contained in user's messages",
        )
        self.assertTrue(user.clear_messages(), msg="cleared users messages")
        self.assertEqual(user.messages, [], msg="messages deleted")

    def test_userinfo_mixin(self):
        """test User.info functionality"""
        user = random_user()
        self.assertIsNone(user.info, msg="info starts out as None")

        info = user.update_info()

        self.assertIsInstance(
            user.info, UserInfo, msg="user info is the correct type"
        )
        self.assertEqual(
            user.info, info, msg="user info is returned after creation"
        )
        self.assertEqual(
            info,
            user.update_info(),
            msg="calling update_info multiple times returns the same object",
        )

    def test_update(self):
        """test User.update()"""
        user = random_user()
        new_first_name = random_first_name()
        new_last_name = random_last_name()
        new_username = random_username()
        new_email = random_email()
        new_password = random_password()
        user.update(
            first_name=new_first_name,
            last_name=new_last_name,
            username=new_username,
            email=new_email,
            password=new_password,
        )
        self.assertEqual(
            user.first_name, new_first_name, msg="first name updated"
        )
        self.assertEqual(
            user.last_name, new_last_name, msg="last name updated"
        )
        self.assertEqual(user.username, new_username, msg="username updated")
        self.assertEqual(user.email, new_email, msg="email updated")
        self.assertTrue(
            user.verify_password(new_password), msg="password updated"
        )

        # updating one attribute doesn't affect the others
        user.update(username=random_username())
        self.assertNotEqual(
            user.username, new_username, msg="username updated"
        )
        self.assertEqual(user.email, new_email, msg="email didn't change")
        self.assertTrue(
            user.verify_password(new_password), msg="password didn't change"
        )

        # protected attributes can't be updated
        # for attr in ("id", "tokens", "messages", "info", "is_admin"):
        #     with self.assertRaises(User.UpdateError) as ctx:
        #         user.update(**{attr: "abc"})
        #     self.assertEqual(
        #         f"cannot update {attr}",
        #         ctx.exception.args[0],
        #         msg=f"can't update attribute {attr}",
        #     )

        # trying to update username or email to an existing one raises an error
        user2 = random_user()
        with self.assertRaises(User.UpdateError) as ctx:
            user.update(username=user2.username)
        self.assertEqual(
            "username is taken",
            ctx.exception.args[0],
            msg="username must be unique",
        )
        with self.assertRaises(User.UpdateError) as ctx:
            user.update(email=user2.email)
        self.assertEqual(
            "email is taken", ctx.exception.args[0], msg="email must be unique"
        )

        # reusing the same username or email doesn't raise an error
        user.update(username=user.username, email=user.email)
