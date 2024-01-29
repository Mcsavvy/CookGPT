"""schema and fields examples."""

UserType = "COOK"
FirstName = "John"
LastName = "Doe"
Username = "johndoe"
Email = "johndoe@example.com"
UserName = "John Doe"
Password = "Password123!"
AuthToken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
AuthType = "Bearer"
Uuid = "36b51f8a-c9fa-43f8-92fa-ff6927736c10"
DateTime = "2021-01-01 00:00:00"
MaxChatCost = 4000
TotalChatCost = 1000
ProfilePicture = "https://example.com/profile.jpg"


UserInfo = {
    "id": Uuid,
    "user_type": UserType,
    "first_name": FirstName,
    "last_name": LastName,
    "username": Username,
    "email": Email,
    "profile_picture": ProfilePicture,
    "max_chat_cost": MaxChatCost,
    "total_chat_cost": TotalChatCost,
}

AuthInfo = {
    "user_id": Uuid,
    "user_name": UserName,
    "atoken": AuthToken,
    "atoken_expiry": DateTime,
    "rtoken": AuthToken,
    "rtoken_expiry": DateTime,
    "user_type": UserType,
    "auth_type": AuthType,
}


class Auth:
    """User signup data examples."""

    class Signup:
        """User signup data examples."""

        Body = {
            "first_name": FirstName,
            "last_name": LastName,
            "username": Username,
            "email": Email,
            "password": Password,
        }
        Response = {
            "message": "Successfully signed up",
            "user": UserInfo,
        }
        Error = {"message": "email is taken"}

    class Login:
        """User login data examples."""

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
        """User logout data examples."""

        Response = {"message": "Logged out user"}

    class Refresh:
        """Token refresh data examples."""

        Response = {
            "message": "Refreshed access token",
            "auth_info": AuthInfo,
        }


class User:
    """User data examples."""

    class Info:
        """User info data examples."""

        Response = UserInfo

    class Update:
        """User update data examples."""

        Body = {
            "first_name": FirstName,
            "last_name": LastName,
            "username": Username,
            "email": Email,
            "password": Password,
        }
        Response = {
            "message": "Successfully updated user",
        }
        Error = {"message": "email is taken"}

    class Delete:
        """User delete data examples."""

        Response = {"message": "Successfully deleted"}
        Error = {"message": "Cannot delete user"}


class UserUpdate:
    """User update data examples."""

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
