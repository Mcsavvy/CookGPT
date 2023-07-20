from apiflask import Schema, fields

from cookgpt.ext.validators import (
    email_validator,
    firstname_validator,
    lastname_validator,
    login_validator,
    password_validator,
    username_validator,
)


class UserSchema(Schema):
    """User schema"""

    username = fields.String(validate=username_validator)
    email = fields.Email(required=True, validate=email_validator)
    first_name = fields.String(required=True, validate=firstname_validator)
    last_name = fields.String(required=True, validate=lastname_validator)
    password = fields.String(required=True, validate=password_validator)


class SignupSchema(Schema):
    """Signup schema"""

    username = fields.String(validate=username_validator)
    email = fields.Email(required=True, validate=email_validator)
    first_name = fields.String(required=True, validate=firstname_validator)
    last_name = fields.String(required=True, validate=lastname_validator)
    password = fields.String(required=True, validate=password_validator)


class LoginSchema(Schema):
    """Login schema"""

    login = fields.String(required=True, validate=login_validator)
    password = fields.String(required=True, validate=password_validator)
