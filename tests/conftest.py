import os
import sys

import pytest

from cookgpt import create_app
from cookgpt.ext.database import db
from cookgpt.user.models import User  # noqa: F401


@pytest.fixture(scope="session")
def app():
    os.environ["FLASK_ENV"] = "testing"
    app = create_app(FORCE_ENV_FOR_DYNACONF="testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.rollback()
        db.drop_all()


@pytest.fixture(autouse=True)
def go_to_tmpdir(request):
    # Get the fixture dynamically by its name.
    tmpdir = request.getfixturevalue("tmpdir")
    # ensure local test created packages can be imported
    sys.path.insert(0, str(tmpdir))
    # Chdir only for the duration of the test.
    with tmpdir.as_cwd():
        yield


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def user(app):
    user = User.create(
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        username="johndoe",
        password="JohnDoe1234",
        commit=True,
    )
    yield user
    user.delete()
