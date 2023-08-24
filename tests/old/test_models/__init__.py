from unittest import TestCase

from .. import User  # noqa: F401
from .. import (Message, MessageMixin, Token, TokenMixin, UserInfo,
                UserInfoMixin, db, purge_all, update_config)


class BaseTestCase(TestCase):
    """base test case for testing models"""

    def tearDown(self) -> None:
        db.session.rollback()
        return super().tearDown()


from .test_basemodel import TestBaseModel  # noqa: F401,E402
from .test_message import TestMessage  # noqa: F401,E402
from .test_token import TestToken  # noqa: F401,E402
from .test_user import TestUser  # noqa: F401,E402
from .test_userinfo import TestUserInfo  # noqa: F401,E402
