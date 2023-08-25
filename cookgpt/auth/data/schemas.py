"""data validation & serialization schemas"""
from apiflask import Schema, fields
from apiflask.schemas import EmptySchema

from . import examples as ex
from . import validators as v


def FirstName(**attrs):
    return fields.String(
        validate=v.FirstName(),
        metadata={"description": "user's first name", "example": ex.FirstName},
        **attrs
    )


def LastName(**attrs):
    return fields.String(
        validate=v.LastName(),
        metadata={"description": "user's last name", "example": ex.LastName},
        **attrs
    )


def Username(**attrs):
    return fields.String(
        validate=v.Username(),
        metadata={"description": "user's username", "example": ex.Username},
        **attrs
    )


def Email(**attrs):
    return fields.String(
        validate=v.Email(),
        metadata={"description": "user's email address", "example": ex.Email},
        **attrs
    )


def Login(**attrs):
    return fields.String(
        validate=v.Login(),
        metadata={
            "description": "user's username or email",
            "example": ex.Email,
        },
        **attrs
    )


def Password(**attrs):
    return fields.String(
        validate=v.Password(),
        metadata={"description": "user's password", "example": ex.Password},
        **attrs
    )


def AuthToken(**attrs):
    return fields.String(
        metadata={
            "description": "a JWT to authenticate as a user to the backend",
            "example": ex.AuthToken,
        },
        **attrs
    )


def UserType(**attrs):
    return fields.String(
        metadata={"description": "the type of user", "example": ex.UserType},
        **attrs
    )


def Datetime(**attrs):
    return fields.DateTime(
        metadata={"description": "a datetime", "example": ex.DateTime}, **attrs
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
