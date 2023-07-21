from apiflask import fields
from marshmallow import ValidationError


def username_validator(username):
    """Username validator"""
    errors = []
    if len(username) < 3:
        errors.append("Username must be at least 3 characters long")
    if len(username) > 20:
        errors.append("Username must be at most 20 characters long")
    if not username.isalnum():
        errors.append("Username must be alphanumeric")
    if errors:
        raise ValidationError(errors)


def password_validator(password):
    """
    Password validator.

    password must be a combination of at least 3 of the following:
    - lowercase letters
    - uppercase letters
    - digits
    - punctuation characters

    password must be at least 8 characters long
    """
    import string

    errors = []
    checks = 0
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    if any(char in string.ascii_lowercase for char in password):
        checks += 1
    if any(char in string.ascii_uppercase for char in password):
        checks += 1
    if any(char in string.digits for char in password):
        checks += 1
    if any(char in string.punctuation for char in password):
        checks += 1
    if checks < 3:
        errors.append(
            "password must contain: lowercase, uppercase, digits, punctuation"
        )
    if errors:
        raise ValidationError(errors)


def email_validator(email):
    """Email validator"""
    fields.Email().deserialize(email)


def firstname_validator(first_name):
    """Firstname validator"""
    errors = []
    if len(first_name) < 3:
        errors.append("Firstname must be at least 3 characters long")
    if len(first_name) > 20:
        errors.append("Firstname must be at most 20 characters long")
    if not first_name.isalpha():
        errors.append("Firstname must be alphabetic")
    if errors:
        raise ValidationError(errors)


def lastname_validator(last_name):
    """Lastname validator"""
    errors = []
    if len(last_name) < 3:
        errors.append("Lastname must be at least 3 characters long")
    if len(last_name) > 20:
        errors.append("Lastname must be at most 20 characters long")
    if not last_name.isalpha():
        errors.append("Lastname must be alphabetic")
    if errors:
        raise ValidationError(errors)


def login_validator(login):
    """Login validator"""
    try:
        email_validator(login)
    except ValidationError:
        try:
            username_validator(login)
        except ValidationError:
            raise ValidationError(["Login must be a valid email or username"])
