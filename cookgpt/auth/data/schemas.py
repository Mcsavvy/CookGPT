"""data validation & serialization schemas"""
from apiflask import Schema, fields

from cookgpt.utils import make_field

from . import examples as ex
from . import validators as v

Id = make_field(fields.UUID, "user's id", ex.Uuid)
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


class User:
    """user data"""

    class In(EmptySchema):
        pass

    class Out(Schema):
        id = fields.UUID(
            metadata={"description": "user's id", "example": ex.Uuid}
        )
        user_type = UserType()
        first_name = FirstName()
        last_name = LastName()
        username = Username()
        email = Email()
        max_chat_cost = fields.Integer(
            metadata={
                "description": "the maximum cost of a user's chat",
                "example": ex.MaxChatCost,
            }
        )
        total_chat_cost = fields.Integer(
            metadata={
                "description": "the total cost of a user's chat",
                "example": ex.TotalChatCost,
            }
        )


class UserCreate:
    """User signup data"""

    class In(Schema):
        first_name = FirstName(required=True)
        last_name = LastName(required=True)
        email = Email(required=True)
        password = Password(required=True)
        username = Username(allow_none=True)

    class Out(Schema):
        message = fields.String()

    class Error(Schema):
        message = fields.String()


class UserLogin:
    """User login data"""

    class In(Schema):
        login = Login(required=True)
        password = Password(required=True)

    class Out(Schema):
        message = fields.String()
        atoken = AuthToken()
        atoken_expiry = Datetime()
        rtoken = AuthToken()
        rtoken_expiry = Datetime()
        user_type = UserType()
        auth_type = fields.String()

        rtoken.metadata[
            "description"
        ] = "a JWT to refresh a user's access token"

    class NotFound(Schema):
        message = fields.String()

    class Unauthorized(Schema):
        message = fields.String()


class UserLogout:
    """User logout data"""

    class In(EmptySchema):
        pass

    class Out(Schema):
        message = fields.String()


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
        user = fields.Nested(User.Out)

    class Error(Schema):
        message = fields.String()


class UserDelete:
    """Delete user data"""

    class In(EmptySchema):
        pass

    class Out(Schema):
        message = fields.String()


class TokenRefresh:
    """Refresh a json web token"""

    class In(EmptySchema):
        pass

    class Out(UserLogin.Out):
        pass
