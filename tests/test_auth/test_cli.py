import pytest
from marshmallow import ValidationError

from cookgpt.auth.cli import create_admin, create_cook
from cookgpt.auth.data.enums import UserType
from cookgpt.auth.models.user import User


@pytest.mark.usefixtures("app")
class TestCreateAdmin:
    """test `auth create-admin`"""

    def test_payload_validation(self, faker):
        """test that the payload is being validated"""
        uname = faker.user_name()
        pword = "2short"  # too short
        fname = "John."  # invalid
        lname = "Doe"
        email = faker.email()

        with pytest.raises(ValidationError) as excinfo:
            create_admin.main(
                [
                    "-f",
                    fname,
                    "-l",
                    lname,
                    "-e",
                    email,
                    "-p",
                    pword,
                    "-u",
                    uname,
                ]
            )
        assert "first_name" in excinfo.value.messages_dict
        assert "password" in excinfo.value.messages_dict
        assert len(excinfo.value.messages_dict) == 2

    def test_create_success(self, faker):
        """test creating an admin"""

        uname = faker.unique.user_name()
        pword = faker.password()
        fname = faker.first_name()
        lname = faker.last_name()
        email = faker.unique.email()

        with pytest.raises(SystemExit) as excinfo:
            create_admin.main(
                [
                    "-f",
                    fname,
                    "-l",
                    lname,
                    "-e",
                    email,
                    "-p",
                    pword,
                    "-u",
                    uname,
                ]
            )
        assert excinfo.value.code == 0
        user = User.query.filter(User.email == email).first()
        assert user is not None
        assert user.first_name == fname
        assert user.last_name == lname
        assert user.email == email
        assert user.password != pword  # hashed
        assert user.username == uname
        assert user.user_type == UserType.ADMIN

    def test_create_no_lastname(self, faker):
        """test creating an admin without last name"""

        fname = faker.first_name()
        email = faker.unique.email()
        pword = faker.password()
        uname = faker.user_name()

        with pytest.raises(SystemExit) as excinfo:
            create_admin.main(
                ["-f", fname, "-e", email, "-p", pword, "-u", uname]
            )
        assert excinfo.value.code == 0
        user = User.query.filter(User.email == email).first()
        assert user is not None
        assert user.first_name == fname
        assert user.last_name is None
        assert user.username == uname
        assert user.email == email
        assert user.password != pword

    def test_create_no_username(self, faker):
        """test creating an admin without username"""

        fname = faker.first_name()
        lname = faker.last_name()
        email = faker.unique.email()
        pword = faker.password()

        with pytest.raises(SystemExit) as excinfo:
            create_admin.main(
                ["-f", fname, "-l", lname, "-e", email, "-p", pword]
            )
        assert excinfo.value.code == 0
        user = User.query.filter(User.email == email).first()
        assert user is not None
        assert user.first_name == fname
        assert user.last_name == lname
        assert user.email == email
        assert user.password != pword  # hashed
        assert user.username is None
        assert user.user_type == UserType.ADMIN

    def test_create_taken_username(self, faker, user):
        """
        test creating an admin when `username`
        has been used by another user
        """
        from contextlib import redirect_stdout
        from io import StringIO

        buffer = StringIO()
        uname = user.username
        fname = faker.first_name()
        lname = faker.last_name()
        email = faker.unique.email()
        pword = faker.password()

        with pytest.raises(SystemExit) as excinfo, redirect_stdout(buffer):
            create_admin.main(
                [
                    "-f",
                    fname,
                    "-l",
                    lname,
                    "-e",
                    email,
                    "-p",
                    pword,
                    "-u",
                    uname,
                    "--allow-existing",
                ]
            )
        assert excinfo.value.code == 0
        buffer.seek(0)
        assert "user with that username already exists" in (buffer.read())

        buffer.seek(0)
        buffer.truncate(0)

        # WITHOUT ALLOWING EXISTING USER

        with pytest.raises(SystemExit) as excinfo, redirect_stdout(buffer):
            create_admin.main(
                [
                    "-f",
                    fname,
                    "-l",
                    lname,
                    "-e",
                    email,
                    "-p",
                    pword,
                    "-u",
                    uname,
                ]
            )
        assert excinfo.value.code == 1
        buffer.seek(0)
        assert "user with that username already exists" in (buffer.read())

    def test_create_taken_email(self, faker, user):
        """
        test creating an admin when `email`
        has been used by another user
        """
        from contextlib import redirect_stdout
        from io import StringIO

        buffer = StringIO()
        uname = faker.unique.user_name()
        fname = faker.first_name()
        lname = faker.last_name()
        email = user.email
        pword = faker.password()

        with pytest.raises(SystemExit) as excinfo, redirect_stdout(buffer):
            create_admin.main(
                [
                    "-f",
                    fname,
                    "-l",
                    lname,
                    "-e",
                    email,
                    "-p",
                    pword,
                    "-u",
                    uname,
                    "--allow-existing",
                ]
            )
        assert excinfo.value.code == 0
        buffer.seek(0)
        assert "user with that email already exists" in (buffer.read())

    def test_create_taken_username_and_email(self, user, faker):
        """
        test creating an admin when `username` and `email`
        has been used by another user
        """
        from contextlib import redirect_stdout
        from io import StringIO

        buffer = StringIO()
        uname = user.username
        fname = faker.first_name()
        lname = faker.last_name()
        email = user.email
        pword = faker.password()

        with pytest.raises(SystemExit) as excinfo, redirect_stdout(buffer):
            create_admin.main(
                [
                    "-f",
                    fname,
                    "-l",
                    lname,
                    "-e",
                    email,
                    "-p",
                    pword,
                    "-u",
                    uname,
                    "--allow-existing",
                ]
            )
        assert excinfo.value.code == 0
        buffer.seek(0)
        assert "user with that username and email already exists" in (
            buffer.read()
        )


@pytest.mark.usefixtures("app")
class TestCreateCook:
    """test `auth create-cook`"""

    def test_create_success(self, faker):
        """test creating a cook"""

        uname = faker.unique.user_name()
        pword = faker.password()
        fname = faker.first_name()
        lname = faker.last_name()
        email = faker.unique.email()

        with pytest.raises(SystemExit) as excinfo:
            create_cook.main(
                [
                    "-f",
                    fname,
                    "-l",
                    lname,
                    "-e",
                    email,
                    "-p",
                    pword,
                    "-u",
                    uname,
                ]
            )
        assert excinfo.value.code == 0
        user = User.query.filter(User.email == email).first()
        assert user is not None
        assert user.first_name == fname
        assert user.last_name == lname
        assert user.email == email
        assert user.password != pword  # hashed
        assert user.username == uname
        assert user.user_type == UserType.COOK


class TestGetAccessToken:
    def test_get_existing_token(self, user: User):
        """test getting an existing token"""
        from click.testing import CliRunner

        from cookgpt.auth import app

        runner = CliRunner()
        token = user.request_token()

        # test with email
        result = runner.invoke(app.cli, ["get-access-token", user.email])
        assert result.exit_code == 0
        assert token.access_token in result.output

        # test with username
        result = runner.invoke(app.cli, ["get-access-token", user.username])
        assert result.exit_code == 0
        assert token.access_token in result.output

    def test_get_new_token(self, user: User):
        """test getting a new token"""
        from click.testing import CliRunner

        from cookgpt.auth import app

        runner = CliRunner()

        assert len(user.tokens) == 0  # type: ignore

        # test with email
        result = runner.invoke(app.cli, ["get-access-token", user.email, "-n"])
        assert result.exit_code == 0
        assert len(user.tokens) == 1  # type: ignore
        token1 = user.tokens[0]  # type: ignore
        assert token1.access_token in result.output

        # test with username
        result = runner.invoke(
            app.cli, ["get-access-token", user.username, "-n"]
        )
        assert result.exit_code == 0
        assert len(user.tokens) == 2  # type: ignore

    def test_get_new_token_no_user(self):
        """test getting a new token for a non-existent user"""
        from click.testing import CliRunner

        from cookgpt.auth import app

        runner = CliRunner()

        # test with email
        result = runner.invoke(app.cli, ["get-access-token", "non-existent"])
        assert result.exit_code == 1
        assert result.exception

        # test with username
        result = runner.invoke(app.cli, ["get-access-token", "non-existent"])
        assert result.exit_code == 1
        assert result.exception
