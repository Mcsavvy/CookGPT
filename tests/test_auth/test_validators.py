"""test validators"""
import pytest

from cookgpt.auth.data.validators import (
    Email,
    FirstName,
    LastName,
    Login,
    Password,
    Username,
    ValidationError,
)

username_validator = Username()
password_validator = Password()
firstname_validator = FirstName()
lastname_validator = LastName()
email_validator = Email()
login_validator = Login()


class TestUsernameValidator:
    """Test username validator"""

    def test_valid_username(self):
        """Test valid usernames"""
        valid_inputs = ["johndoe", "john_doe", "john1", "john-doe"]
        for username in valid_inputs:
            assert username_validator(username) == username

    def test_invalid_username(self):
        """test different invalid usernames"""
        invalid_inputs = [
            ["_john", Username.START_ERR],
            ["j", Username.LENGTH_ERR],
            ["d" * 46, Username.LENGTH_ERR],
            ["-007-", Username.LETTER_ERR],
            ["john$", Username.CHARSET_ERR],
        ]
        for username, expected_error in invalid_inputs:
            with pytest.raises(ValidationError) as excinfo:
                assert username_validator(username) == username
            assert expected_error in excinfo.value.messages


class TestPasswordValidator:
    """Test password validator"""

    def test_password_validator_too_short(self):
        """Test a password that is too short"""
        password = "passwrd"
        with pytest.raises(ValidationError) as excinfo:
            password_validator(password)
        assert Password.LENGTH_ERR in excinfo.value.messages

    def test_invalid_password(self):
        """Test a password that doesn't contain uppercase"""
        P = Password
        invalid_inputs = [
            [
                "password",
                (  # only lowercase
                    P.UPPERCASE_ERR,
                    P.DIGIT_ERR,
                    P.PUNCTUATION_ERR,
                ),
            ],
            [
                "password123",
                (  # only lowercase and digits
                    P.UPPERCASE_ERR,
                    P.PUNCTUATION_ERR,
                ),
            ],
            [
                "password!",
                (  # only lowercase and punctuation
                    P.UPPERCASE_ERR,
                    P.DIGIT_ERR,
                ),
            ],
            [
                "PASSWORD",
                (  # only uppercase
                    P.LOWERCASE_ERR,
                    P.DIGIT_ERR,
                    P.PUNCTUATION_ERR,
                ),
            ],
            [
                "PASSWORD123",
                (  # only uppercase and digits
                    P.LOWERCASE_ERR,
                    P.PUNCTUATION_ERR,
                ),
            ],
            [
                "PASSWORD!",
                (  # only uppercase and punctuation
                    P.LOWERCASE_ERR,
                    P.DIGIT_ERR,
                ),
            ],
            [
                "12345678",
                (  # only digits
                    P.UPPERCASE_ERR,
                    P.LOWERCASE_ERR,
                    P.PUNCTUATION_ERR,
                ),
            ],
            [
                "12345678!",
                (  # only digits and punctuation
                    P.UPPERCASE_ERR,
                    P.LOWERCASE_ERR,
                ),
            ],
            [
                "!@#$%^&*()",
                (  # only punctuation
                    P.UPPERCASE_ERR,
                    P.LOWERCASE_ERR,
                    P.DIGIT_ERR,
                ),
            ],
        ]

        for password, expected_errors in invalid_inputs:
            with pytest.raises(ValidationError) as excinfo:
                password_validator(password)
            for error in expected_errors:
                assert error in excinfo.value.messages

    def test_valid_password(self):
        """Test that a password is valid"""

        valid_passwords = [
            "Password123!",  # lowercase, uppercase, digits, punctuation
            "Password!",  # lowercase, uppercase, punctuation
            "Password123",  # lowercase, uppercase, digits
            "password123!",  # lowercase, digits, punctuation
            "PASSWORD123!",  # uppercase, digits, punctuation
        ]

        for password in valid_passwords:
            assert password_validator(password) == password


class TestEmailValidator:
    """Test email validator"""

    def test_valid_email(self):
        """Test a valid email"""
        email = "john.doe@example.com"
        assert email_validator(email) is email

    def test_invalid_email(self):
        """Test an invalid email"""
        email = "johndoe@example"
        with pytest.raises(ValidationError) as excinfo:
            email_validator(email)
        assert Email.FORMAT_ERR in excinfo.value.messages


class TestFirstnameValidator:
    """Test firstname validator"""

    def test_invalid_first_names(self):
        """Test invalid first names"""
        invalid_inputs = [
            ["John_", FirstName.CHARSET_ERR],
            ["John1", FirstName.CHARSET_ERR],
            ["J", FirstName.LENGTH_ERR],
            ["J" * 26, FirstName.LENGTH_ERR],
        ]
        for fname, expected_error in invalid_inputs:
            with pytest.raises(ValidationError) as excinfo:
                firstname_validator(fname)
            assert expected_error in excinfo.value.messages

    def test_valid_first_names(self, faker):
        """Test valid first names"""

        for _ in range(10):
            fname = faker.first_name()
            assert firstname_validator(fname) == fname


class TestLastnameValidator:
    """Test firstname validator"""

    def test_invalid_lastnames(self):
        """Test invalid first names"""
        invalid_inputs = [
            ["John_", FirstName.CHARSET_ERR],
            ["John1", FirstName.CHARSET_ERR],
            ["J", FirstName.LENGTH_ERR],
            ["J" * 26, FirstName.LENGTH_ERR],
        ]
        for lastname, expected_error in invalid_inputs:
            with pytest.raises(ValidationError) as excinfo:
                firstname_validator(lastname)
            assert expected_error in excinfo.value.messages

    def test_valid_lastnames(self, faker):
        """Test valid first names"""

        for _ in range(10):
            lname = faker.last_name()
            assert firstname_validator(lname) == lname


class TestLoginValidator:
    def test_login_validator_valid_email(self):
        """Test a valid email login"""
        email = "john.doe@example.com"
        assert login_validator(email) == email

    def test_login_validator_valid_username(self):
        """Test a valid username login"""
        username = "johndoe"
        assert login_validator(username) == username

    def test_login_validator_invalid(self):
        """Test an invalid login"""
        login = "johndoe@example"
        with pytest.raises(ValidationError) as excinfo:
            login_validator(login)
        assert Login.FORMAT_ERR in excinfo.value.messages
