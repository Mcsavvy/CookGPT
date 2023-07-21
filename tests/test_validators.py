"""test validators"""
import pytest

from cookgpt.ext.validators import (
    ValidationError,
    email_validator,
    firstname_validator,
    lastname_validator,
    login_validator,
    password_validator,
    username_validator,
)


class TestUsernameValidator:
    """Test username validator"""

    def test_username_validator_valid(self):
        """Test a valid username"""
        username = "johndoe"
        assert username_validator(username) is None

    def test_username_validator_too_short(self):
        """Test a username that is too short"""
        username = "jd"
        with pytest.raises(ValidationError) as excinfo:
            username_validator(username)
        assert "Username must be at least 3 characters long" in str(
            excinfo.value
        )

    def test_username_validator_too_long(self):
        """Test a username that is too long"""
        username = "johndoe123456789012345"
        with pytest.raises(ValidationError) as excinfo:
            username_validator(username)
        assert "Username must be at most 20 characters long" in str(
            excinfo.value
        )

    def test_username_validator_non_alphanumeric(self):
        """Test a username that is not alphanumeric"""
        username = "john.doe"
        with pytest.raises(ValidationError) as excinfo:
            username_validator(username)
        assert "Username must be alphanumeric" in str(excinfo.value)


class TestPasswordValidator:
    def test_password_validator_valid(self):
        """Test a valid password"""
        password = "Password123!"
        assert password_validator(password) is None

    def test_password_validator_too_short(self):
        """Test a password that is too short"""
        password = "passwrd"
        with pytest.raises(ValidationError) as excinfo:
            password_validator(password)
        assert "Password must be at least 8 characters long" in str(
            excinfo.value
        )

    def test_password_invalid(self):
        """Test a password is invalid"""

        invalid_passwords = [
            "password",  # only lowercase
            "password123",  # only lowercase and digits
            "password!",  # only lowercase and punctuation
            "PASSWORD",  # only uppercase
            "PASSWORD123",  # only uppercase and digits
            "PASSWORD!",  # only uppercase and punctuation
            "12345678",  # only digits
            "12345678!",  # only digits and punctuation
            "!@#$%^&*()",  # only punctuation
        ]
        # a valid password must contain at least 3 of the following:
        # - lowercase letters
        # - uppercase letters
        # - digits
        # - punctuation characters
        valid_passwords = [
            "Password123!",  # lowercase, uppercase, digits, punctuation
            "Password!",  # lowercase, uppercase, punctuation
            "Password123",  # lowercase, uppercase, digits
            "password123!",  # lowercase, digits, punctuation
            "PASSWORD123!",  # uppercase, digits, punctuation
        ]
        for password in invalid_passwords:
            with pytest.raises(ValidationError) as excinfo:
                password_validator(password)
            assert (
                "password must contain: "
                "lowercase, uppercase, digits, punctuation"
            ) in str(excinfo.value)
        for password in valid_passwords:
            assert password_validator(password) is None


class TestEmailValidator:
    """Test email validator"""

    def test_email_validator_valid(self):
        """Test a valid email"""
        email = "john.doe@example.com"
        assert email_validator(email) is None

    def test_email_validator_invalid(self):
        """Test an invalid email"""
        email = "johndoe@example"
        with pytest.raises(ValidationError) as excinfo:
            email_validator(email)
        assert "Not a valid email address." in str(excinfo.value)


class TestFirstnameValidator:
    """Test firstname validator"""

    def test_firstname_validator_valid(self):
        """Test a valid firstname"""
        firstname = "John"
        assert firstname_validator(firstname) is None

    def test_firstname_validator_too_short(self):
        """Test a firstname that is too short"""
        firstname = "Jo"
        with pytest.raises(ValidationError) as excinfo:
            firstname_validator(firstname)
        assert "Firstname must be at least 3 characters long" in str(
            excinfo.value
        )

    def test_firstname_validator_too_long(self):
        """Test a firstname that is too long"""
        firstname = "John12345678901234567"
        with pytest.raises(ValidationError) as excinfo:
            firstname_validator(firstname)
        assert "Firstname must be at most 20 characters long" in str(
            excinfo.value
        )


class TestLastNameValidator:
    """Test lastname validator"""

    def test_lastname_validator_valid(self):
        """Test a valid lastname"""
        lastname = "Doe"
        assert lastname_validator(lastname) is None

    def test_lastname_validator_too_short(self):
        """Test a lastname that is too short"""
        lastname = "Do"
        with pytest.raises(ValidationError) as excinfo:
            lastname_validator(lastname)
        assert "Lastname must be at least 3 characters long" in str(
            excinfo.value
        )

    def test_lastname_validator_too_long(self):
        """Test a lastname that is too long"""
        lastname = "Doe123456789012345678"
        with pytest.raises(ValidationError) as excinfo:
            lastname_validator(lastname)
        assert "Lastname must be at most 20 characters long" in str(
            excinfo.value
        )


class TestLoginValidator:
    def test_login_validator_valid_email(self):
        """Test a valid email login"""
        login = "john.doe@example.com"
        assert login_validator(login) is None

    def test_login_validator_valid_username(self):
        """Test a valid username login"""
        login = "johndoe"
        assert login_validator(login) is None
        login = "john.doe@gmail.com"
        assert login_validator(login) is None

    def test_login_validator_invalid(self):
        """Test an invalid login"""
        login = "johndoe@example"
        with pytest.raises(ValidationError) as excinfo:
            login_validator(login)
        assert "Login must be a valid email or username" in str(excinfo.value)
