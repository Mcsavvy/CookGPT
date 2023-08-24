"""test base model"""
from unittest.mock import patch
from uuid import UUID

from cookgpt.models import BaseModel, User, db

from .. import random_user
from . import BaseTestCase


class TestBaseModel(BaseTestCase):
    """test base model"""

    def test_init(self):
        """test base model"""
        with patch.object(
            BaseModel, "__init__", return_value=None
        ) as mock_init:
            user = random_user(save=False)
            mock_init.assert_called_once()
        user = random_user(save=False)
        self.assertIsInstance(
            user, BaseModel, msg="user is an instance of BaseModel"
        )
        self.assertIsNone(user.id, msg="id is not yet set")
        self.assertTrue(
            db.session.is_modified(user), msg="user has not been saved"
        )

    def test_save(self):
        """test BaseModel.save()"""
        user = random_user(save=False)
        self.assertIsNone(user.id, msg="id is not yet set")
        user.save()
        self.assertIsInstance(user.id, UUID, msg="id is set")
        self.assertFalse(
            db.session.is_modified(user), msg="user has been saved"
        )

    def test_delete(self):
        """test BaseModel.delete()"""
        user = random_user()
        user.delete()
        self.assertIsNone(
            db.session.get(User, user.id),
            msg="user has been deleted",
        )

    def test_update(self):
        """test BaseModel.update()"""
        model = BaseModel()
        with patch.object(BaseModel, "save", return_value=None) as mock_save:
            model.update(name="test", email="test@gmail.com")
            mock_save.assert_called_once()
        self.assertEqual(
            getattr(model, "name"), "test", msg="name has been updated"
        )
        self.assertEqual(
            getattr(model, "email"),
            "test@gmail.com",
            msg="email has been updated",
        )
        setattr(model, "__protected__", ("id", "name", "email"))
        for attr in model.__protected__:
            with self.assertRaises(model.UpdateError) as cm:
                model.update(**{attr: "test"})
            self.assertEqual(
                str(cm.exception),
                f"cannot update {attr}",
                msg=f"cannot update protected attribute {attr}",
            )
