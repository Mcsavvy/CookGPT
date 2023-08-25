"""schema and fields examples"""

UserType = "patient"
FirstName = "John"
LastName = "Doe"
Username = "johndoe"
Email = "johndoe@example.com"
Password = "Password123!"
AuthToken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
Uuid = "36b51f8a-c9fa-43f8-92fa-ff6927736c10"
DateTime = "2021-01-01 00:00:00"
MaxChatCost = 4000
TotalChatCost = 1000


class User:
    """user data examples"""

    Out = {
        "id": Uuid,
        "user_type": UserType,
        "first_name": FirstName,
        "last_name": LastName,
        "username": Username,
        "max_chat_cost": MaxChatCost,
        "total_chat_cost": TotalChatCost,
    }


class UserCreate:
    """User signup data examples"""

    In = {
        "first_name": FirstName,
        "last_name": LastName,
        "username": Username,
        "email": Email,
        "password": Password,
    }
    Out = {"message": "Successfully signed up"}
    Error = {"message": "email is taken"}


class UserUpdate:
    """User update data examples"""

    In = {
        "first_name": FirstName,
        "last_name": LastName,
        "username": Username,
        "email": Email,
        "password": Password,
    }
    Out = {
        "message": "Successfully updated",
        "user": User.Out,
    }
    Error = {"message": "email is taken"}


class UserLogin:
    """User login data examples"""

    In = {
        "login": Username,
        "password": Password,
    }
    Out = {
        "message": "Successfully logged in",
        "atoken": AuthToken,
        "atoken_expiry": DateTime,
        "rtoken": AuthToken,
        "rtoken_expiry": DateTime,
        "user_type": UserType,
        "auth_type": "Bearer",
    }
    NotFound = {
        "message": "User does not exist",
    }
    Unauthorized = {
        "message": "Cannot authenticate",
    }


class UserLogout:
    """User logout data examples"""

    Out = {"message": "Logged out user"}


class UserDelete:
    """User delete data examples"""

    Out = {
        "message": "user deleted",
    }


class TokenRefresh:
    """token refresh data example"""

    Out = {
        "message": "Refreshed access token",
        "atoken": AuthToken,
        "atoken_expiry": DateTime,
        "rtoken": AuthToken,
        "rtoken_expiry": DateTime,
        "user_type": UserType,
        "auth_type": "Bearer",
    }
