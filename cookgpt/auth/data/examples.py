"""schema and fields examples"""

UserType = "cook"
FirstName = "John"
LastName = "Doe"
Username = "johndoe"
Email = "johndoe@example.com"
Password = "Password123!"
AuthToken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
AuthType = "Bearer"
Uuid = "36b51f8a-c9fa-43f8-92fa-ff6927736c10"
DateTime = "2021-01-01 00:00:00"
MaxChatCost = 4000
TotalChatCost = 1000


User = {
    "id": Uuid,
    "user_type": UserType,
    "first_name": FirstName,
    "last_name": LastName,
    "username": Username,
    "max_chat_cost": MaxChatCost,
    "total_chat_cost": TotalChatCost,
}

AuthInfo = {
    "atoken": AuthToken,
    "atoken_expiry": DateTime,
    "rtoken": AuthToken,
    "rtoken_expiry": DateTime,
    "user_type": UserType,
    "auth_type": AuthType,
}


class Auth:
    """User signup data examples"""

    class Signup:
        Body = {
            "first_name": FirstName,
            "last_name": LastName,
            "username": Username,
            "email": Email,
            "password": Password,
        }
        Response = {
            "message": "Successfully signed up",
            "user": User,
        }
        Error = {"message": "email is taken"}

    class Login:
        Body = {
            "login": Username,
            "password": Password,
        }
        Response = {
            "message": "Successfully logged in",
            "auth_info": AuthInfo,
        }
        NotFound = {
            "message": "User does not exist",
        }
        Unauthorized = {
            "message": "Cannot authenticate",
        }

    class Logout:
        Response = {"message": "Logged out user"}

    class Refresh:
        Response = {
            "message": "Refreshed access token",
            "auth_info": AuthInfo,
        }


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
        "user": User,
    }
    Error = {"message": "email is taken"}
