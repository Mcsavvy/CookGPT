"""
Test User <-> AI messages
"""
from cookgpt.models import Message
from cookgpt.utils import utcnow

from .. import random_user, random_username
from . import BaseTestCase


class TestMessage(BaseTestCase):
    """test the message model"""

    def test_init(self):
        """test model creation"""
        # though this is beyond our immediate control at the moments,
        # we can still use this to raise signals when something unexpectedly
        # goes wrong
        username = random_username()
        user = random_user(username=username)
        with self.assertRaises(ValueError) as ctx:
            Message(content=None, user=None)
        self.assertEqual(str(ctx.exception), "Message user cannot be empty")
        with self.assertRaises(ValueError) as ctx:
            Message(content=None, user=user)
        self.assertEqual(str(ctx.exception), "Message content cannot be empty")
        with self.assertRaises(ValueError) as ctx:
            Message(content="hi", user=user, response="hi")
        self.assertEqual(str(ctx.exception), "Message cost not supplied")
        with self.assertRaises(ValueError) as ctx:
            Message(content="hi", user=user, response="hi", cost=0)
        self.assertEqual(
            str(ctx.exception), "Message cost must be greater than 0"
        )

        now1 = utcnow()
        msg = Message(content="hi there!", user=user)
        now2 = utcnow()
        msg.save()
        self.assertEqual(msg.user, user, msg="correct user")
        self.assertEqual(
            msg.content, "hi there!", msg="correct message content"
        )
        self.assertGreaterEqual(msg.sent_at, now1, msg="correct sent time")
        self.assertLessEqual(msg.sent_at, now2, msg="correct sent time")
        self.assertIsNone(msg.response, msg="no response yet")
        self.assertIsNone(msg.responded_at, msg="no response yet")

    def test_create(self):
        """test Message.create()"""
        user = random_user()
        before_send = utcnow()
        msg1 = Message.create("hi there!", user)
        after_send = utcnow()
        self.assertEqual(msg1.user, user, msg="correct user")
        self.assertEqual(
            msg1.content, "hi there!", msg="correct message content"
        )
        self.assertGreaterEqual(
            msg1.sent_at, before_send, msg="correct sent time"
        )
        self.assertLessEqual(msg1.sent_at, after_send, msg="correct sent time")
        self.assertIsNone(msg1.response, msg="no response yet")
        self.assertIsNone(msg1.responded_at, msg="no response yet")

        before_send = utcnow()
        msg2 = Message.create("hi there!", user, response="hi", cost=1)
        after_send = utcnow()
        self.assertEqual(msg2.user, user, msg="correct user")
        self.assertEqual(
            msg2.content, "hi there!", msg="correct message content"
        )
        self.assertGreaterEqual(
            msg2.sent_at, before_send, msg="correct sent time"
        )
        self.assertLessEqual(msg2.sent_at, after_send, msg="correct sent time")
        self.assertEqual(msg2.response, "hi", msg="correct response")
        self.assertGreaterEqual(
            msg2.responded_at, before_send, msg="correct response time"
        )
        self.assertLessEqual(
            msg2.responded_at, after_send, msg="correct response time"
        )

    def test_update_response(self):
        """test Message.update_response()"""
        user = random_user()
        msg = Message.create("hi there!", user)

        with self.assertRaises(ValueError) as ctx:
            msg.update_response(None, 1)
        self.assertEqual(
            str(ctx.exception), "Message response cannot be empty"
        )
        with self.assertRaises(ValueError) as ctx:
            msg.update_response("hi", None)
        self.assertEqual(str(ctx.exception), "Message cost not supplied")
        with self.assertRaises(ValueError) as ctx:
            msg.update_response("hi", 0)
        self.assertEqual(
            str(ctx.exception), "Message cost must be greater than 0"
        )

        before_update = utcnow()
        msg.update_response("hi", 1)
        after_update = utcnow()
        self.assertEqual(msg.response, "hi", msg="correct response")
        self.assertEqual(msg.cost, 1, msg="correct cost")
        self.assertGreaterEqual(
            msg.responded_at, before_update, msg="correct response time"
        )
        self.assertLessEqual(
            msg.responded_at, after_update, msg="correct response time"
        )

        before_update = utcnow()
        msg.update_response("hello", 5)
        after_update = utcnow()
        self.assertEqual(msg.response, "hello", msg="correct response")
        self.assertEqual(msg.cost, 5, msg="correct cost")
        self.assertGreaterEqual(
            msg.responded_at, before_update, msg="correct response time"
        )
        self.assertLessEqual(
            msg.responded_at, after_update, msg="correct response time"
        )

    def test_serialize(self):
        """test Message.serialize()"""
        user = random_user()
        msg = Message.create("hi there!", user)
        json = msg.serialize()

        self.assertEqual(json["id"], msg.get_id(), msg="correct id")
        self.assertEqual(json["user"], user.get_id(), msg="correct user")
        self.assertEqual(
            json["query"], "hi there!", msg="correct message content"
        )
        self.assertEqual(
            json["sent_at"], msg.sent_at.isoformat(), msg="correct sent time"
        )
        self.assertIsNone(json["response"], msg="no response yet")
        self.assertIsNone(json["responded_at"], msg="no response yet")

        msg.update_response("hi", 1)
        json = msg.serialize()
        self.assertEqual(json["id"], msg.get_id(), msg="correct id")
        self.assertEqual(json["user"], user.get_id(), msg="correct user")
        self.assertEqual(
            json["query"], "hi there!", msg="correct message content"
        )
        self.assertEqual(
            json["sent_at"], msg.sent_at.isoformat(), msg="correct sent time"
        )
        self.assertEqual(json["response"], "hi", msg="correct response")
        self.assertEqual(
            json["responded_at"],
            msg.responded_at.isoformat(),
            msg="correct response time",
        )
