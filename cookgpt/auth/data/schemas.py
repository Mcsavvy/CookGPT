"""data validation & serialization schemas"""
from apiflask import Schema, fields

from cookgpt.utils import make_field

from . import examples as ex
from . import validators as v

UserID = make_field(fields.UUID, "user's id", ex.Uuid)
UserName = make_field(
    fields.String, "user's name", ex.UserName, validate=v.FirstNameOrFullName()
)
FirstName = make_field(
    fields.String,
    "user's first name",
    ex.FirstName,
    validate=v.FirstName(),
)

LastName = make_field(
    fields.String,
    "user's last name",
    ex.LastName,
    validate=v.LastName(),
)

Username = make_field(
    fields.String,
    "user's username",
    ex.Username,
    validate=v.Username(),
)

Email = make_field(
    fields.String,
    "user's email address",
    ex.Email,
    validate=v.Email(),
)

Login = make_field(
    fields.String,
    "user's username or email",
    ex.Email,
    validate=v.Login(),
)

Password = make_field(
    fields.String,
    "user's password",
    ex.Password,
    validate=v.Password(),
)

AuthToken = make_field(
    fields.String,
    example=ex.AuthToken,
)

UserType = make_field(
    fields.String,
    "the type of user",
    ex.UserType,
)

Datetime = make_field(
    fields.DateTime,
    example=ex.DateTime,
)


class UserSchema(Schema):
    """user schema"""

    id = UserID()
    first_name = FirstName()
    last_name = LastName()
    username = Username()
    email = Email()
    max_chat_cost = fields.Integer(
        metadata={
            "description": "the maximum allowed cost of a user's chat",
            "example": ex.MaxChatCost,
        }
    )
    total_chat_cost = fields.Integer(
        metadata={
            "description": "the total cost of a user's chat",
            "example": ex.TotalChatCost,
        }
    )


class AuthInfoSchema(Schema):
    """user auth info schema"""

    user_id = UserID()
    user_name = UserName()
    atoken = AuthToken(
        metadata={
            "description": "a JWT to authenticate a user",
        }
    )
    atoken_expiry = Datetime(
        metadata={
            "description": "the time the access token expires",
        }
    )
    rtoken = AuthToken(
        metadata={
            "description": "a JWT to refresh a user's access token",
        }
    )
    rtoken_expiry = Datetime(
        metadata={
            "description": "the time the refresh token expires",
        }
    )
    user_type = UserType()
    auth_type = fields.String(
        metadata={
            "description": "the type of authentication",
            "example": ex.AuthType,
        }
    )


class Auth:
    """user data"""

    class Signup:
        class Body(Schema):
            first_name = UserName(required=True)
            last_name = LastName(required=False, allow_none=True)
            email = Email(required=True)
            password = Password(required=True)
            username = Username(allow_none=True, required=False)

        class Response(Schema):
            message = fields.String(
                metadata={
                    "description": "success message",
                    "example": ex.Auth.Signup.Response["message"],
                }
            )

        class Error(Schema):
            message = fields.String(
                metadata={
                    "description": "error message",
                    "example": ex.Auth.Signup.Error["message"],
                }
            )

    class Login:
        class Body(Schema):
            login = Login(required=True)
            password = Password(required=True)

        class Response(Schema):
            message = fields.String(
                metadata={
                    "description": "success message",
                    "example": ex.Auth.Login.Response["message"],
                }
            )
            auth_info = fields.Nested(AuthInfoSchema)

        class NotFound(Schema):
            message = fields.String(
                metadata={
                    "description": "error message",
                    "example": ex.Auth.Login.NotFound["message"],
                }
            )

        class Unauthorized(Schema):
            message = fields.String(
                metadata={
                    "description": "error message",
                    "example": ex.Auth.Login.Unauthorized["message"],
                }
            )

    class Logout:
        class Response(Schema):
            message = fields.String(
                metadata={
                    "description": "success message",
                    "example": ex.Auth.Logout.Response["message"],
                }
            )

    class Refresh:
        class Response(Schema):
            message = fields.String(
                metadata={
                    "description": "success message",
                    "example": ex.Auth.Refresh.Response["message"],
                }
            )
            auth_info = fields.Nested(AuthInfoSchema)


class UserUpdate:
    """Update user data"""

    class In(Schema):
        first_name = FirstName()
        last_name = LastName()
        email = Email()
        password = Password()
        username = Username()

    class Out(Schema):
        message = fields.String()
        user = fields.Nested(UserSchema)

    class Error(Schema):
        message = fields.String()


class UserDelete:
    """Delete user data"""

    class In(Schema):
        pass

    class Out(Schema):
        message = fields.String()
