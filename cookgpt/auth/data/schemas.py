"""data validation & serialization schemas."""
from apiflask import Schema, fields

from cookgpt.auth.data.enums import UserType as UserT
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
    fields.Enum,
    "the type of user",
    ex.UserType,
    UserT,
)

Datetime = make_field(
    fields.DateTime,
    example=ex.DateTime,
)

ProfilePicture = make_field(
    fields.URL,
    "the url of the user's profile picture",
    ex.ProfilePicture,
)

MaxChatCost = make_field(
    fields.Integer,
    "the maximum allowed cost of a user's chat",
    ex.MaxChatCost,
)

TotalChatCost = make_field(
    fields.Integer,
    "the total cost of a user's chat",
    ex.TotalChatCost,
)


class UserSchema(Schema):
    """user schema."""

    id = UserID()
    first_name = FirstName()
    last_name = LastName()
    username = Username()
    email = Email()
    user_type = UserType()  # type: ignore
    profile_picture = ProfilePicture()
    max_chat_cost = MaxChatCost()
    total_chat_cost = TotalChatCost()


class AuthInfoSchema(Schema):
    """user auth info schema."""

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
    user_type = UserType()  # type: ignore
    auth_type = fields.String(
        metadata={
            "description": "the type of authentication",
            "example": ex.AuthType,
        }
    )


class Auth:
    """User authentication operations group."""

    class Signup:
        """User signup operations schema."""

        class Body(Schema):
            """User signup request body schema."""

            first_name = UserName(required=True)
            last_name = LastName(required=False, allow_none=True)
            email = Email(required=True)
            password = Password(required=True)
            username = Username(allow_none=True, required=False)

        class Response(Schema):
            """User signup response schema."""

            message = fields.String(
                metadata={
                    "description": "success message",
                    "example": ex.Auth.Signup.Response["message"],
                }
            )

        class Error(Schema):
            """User signup error schema."""

            message = fields.String(
                metadata={
                    "description": "error message",
                    "example": ex.Auth.Signup.Error["message"],
                }
            )

    class Login:
        """User login operations schema."""

        class Body(Schema):
            """User login request body schema."""

            login = Login(required=True)
            password = Password(required=True)

        class Response(Schema):
            """User login response schema."""

            message = fields.String(
                metadata={
                    "description": "success message",
                    "example": ex.Auth.Login.Response["message"],
                }
            )
            auth_info = fields.Nested(AuthInfoSchema)

        class NotFound(Schema):
            """User login not found error schema."""

            message = fields.String(
                metadata={
                    "description": "error message",
                    "example": ex.Auth.Login.NotFound["message"],
                }
            )

        class Unauthorized(Schema):
            """User login unauthorized error schema."""

            message = fields.String(
                metadata={
                    "description": "error message",
                    "example": ex.Auth.Login.Unauthorized["message"],
                }
            )

    class Logout:
        """User logout operations schema."""

        class Response(Schema):
            """User logout response schema."""

            message = fields.String(
                metadata={
                    "description": "success message",
                    "example": ex.Auth.Logout.Response["message"],
                }
            )

    class Refresh:
        """User token refresh operations schema."""

        class Response(Schema):
            """User token refresh response schema."""

            message = fields.String(
                metadata={
                    "description": "success message",
                    "example": ex.Auth.Refresh.Response["message"],
                }
            )
            auth_info = fields.Nested(AuthInfoSchema)


class User:
    """User operations group."""

    class Info:
        """User info operations schema."""

        class Response(UserSchema):
            """User info response schema."""

            pass

    class Update:
        """User update operations schema."""

        class Body(Schema):
            """User update request body schema."""

            first_name = FirstName()
            last_name = LastName()
            email = Email()
            password = Password()
            username = Username()

        class Response(Schema):
            """User update response schema."""

            message = fields.String(
                metadata={
                    "description": "success message",
                    "example": ex.User.Update.Response["message"],
                }
            )

        class Error(Schema):
            """User update error schema."""

            message = fields.String(
                metadata={
                    "description": "error message",
                    "example": ex.User.Update.Error["message"],
                }
            )

    class Delete:
        """Delete user data."""

        class Response(Schema):
            """User delete response schema."""

            message = fields.String(
                metadata={
                    "description": "success message",
                    "example": ex.User.Delete.Response["message"],
                }
            )

        class Error(Schema):
            """User delete error schema."""

            message = fields.String(
                metadata={
                    "description": "error message",
                    "example": ex.User.Delete.Error["message"],
                }
            )
