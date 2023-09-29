from typing import Any, Optional, cast
from uuid import UUID

# from apiflask.views import MethodView
from flask_jwt_extended import get_current_user, get_jwt

from cookgpt import docs
from cookgpt.auth import app
from cookgpt.auth.data import examples as ex

# from cookgpt.auth.data.schemas import User as UserSchema
from cookgpt.auth.data.schemas import (  # UserDelete,; UserUpdate,
    TokenRefresh,
    UserCreate,
    UserLogin,
    UserLogout,
)
from cookgpt.auth.models import Token
from cookgpt.ext.auth import auth_required
from cookgpt.ext.database import db
from cookgpt.utils import abort, api_output


@app.post("/login")
@app.input(UserLogin.In, example=ex.UserLogin.In)
@app.output(
    UserLogin.Out,
    200,
    example=ex.UserLogin.Out,
    description="Authentication info",
)
@api_output(
    UserLogin.NotFound,
    404,
    example=ex.UserLogin.Unauthorized,
    description="Error message if user does not exist",
)
@api_output(
    UserLogin.Unauthorized,
    401,
    example=ex.UserLogin.Unauthorized,
    description="Error message if password is incorrect",
)
@app.doc(description=docs.AUTH_LOGIN)
def login(json_data: dict) -> Any:
    """Log a user into the system."""
    from cookgpt.auth.models import User

    login: str = json_data["login"]
    password: str = json_data["password"]
    user: Optional[User]

    user = User.query.filter(
        (User.username == login) | (User.email == login)
    ).first()
    if user is None:
        abort(404, "User does not exist")
    elif not user.validate_password(password):
        abort(401, "Cannot authenticate")
    token: "Token" = user.request_token()
    return {
        "message": "Successfully logged in",
        "atoken": token.access_token,
        "atoken_expiry": token.atoken_expiry,
        "rtoken": token.refresh_token,
        "rtoken_expiry": token.rtoken_expiry,
        "user_type": user.get_type(),
        "auth_type": "Bearer",
    }


@app.post("/logout")
@auth_required()
@app.output(
    UserLogout.Out,
    200,
    example=ex.UserLogout.Out,
    description="Success message",
)
@app.doc(description=docs.AUTH_LOGOUT)
def logout() -> Any:
    """Log a user out of the system."""
    from cookgpt.auth.models import User

    jwt = get_jwt()
    user: "User" = get_current_user()
    token = db.session.get(Token, UUID(jwt["jti"]))
    assert token is not None
    user.deactivate_token(token)
    return {"message": "Logged out user"}


@app.post("/signup")
@app.input(UserCreate.In, example=ex.UserCreate.In)
@app.output(
    UserCreate.Out,
    201,
    example=ex.UserCreate.Out,
    description="Success message",
)
@api_output(
    UserCreate.Error,
    422,
    example=ex.UserCreate.Error,
    description="Error message while creating user",
)
@app.doc(description=docs.AUTH_SIGNUP)
def signup(json_data: dict) -> Any:
    """Signup a new user."""
    from cookgpt.auth.models import User

    try:
        User.create(**json_data, user_type=UserType.COOK)
    except User.CreateError as err:
        return {"message": err.args[0]}, 422
    return {"message": "Successfully signed up"}, 201


@app.post("/refresh")
@auth_required(refresh=True)
@app.output(
    TokenRefresh.Out,
    200,
    example=ex.TokenRefresh.Out,
    description="Authentication info",
)
@app.doc(description=docs.AUTH_REFRESH)
def refresh() -> Any:
    """Refresh the access token."""
    jti = UUID(get_jwt()["jti"])
    token = cast(Token, db.session.get(Token, jti))
    token.refresh()
    return {
        "message": "Refreshed access token",
        "atoken": token.access_token,
        "atoken_expiry": token.atoken_expiry,
        "rtoken": token.refresh_token,
        "rtoken_expiry": token.rtoken_expiry,
        "user_type": token.user.get_type(),
        "auth_type": "Bearer",
    }


# class UserView(MethodView):
#     """User view"""

#     decorators = [auth_required]

#     @app.output(UserSchema.Out, example=ex.User.Out)
#     def get(self):
#         """get user details"""
#         user = get_current_user()
#         return user

#     @app.input(UserUpdate.In, example=ex.UserUpdate.In)
#     @app.output(UserUpdate.Out, example=ex.UserUpdate.Out)
#     def patch(self, json_data):
#         """update user details"""
#         from cookgpt.models import User

#         user: User = get_current_user()  # type: ignore
#         user.update(**json_data)
#         return user

#     @app.output(UserDelete.Out, example=ex.UserDelete.Out)
#     def delete(self):
#         """delete user"""
#         from cookgpt.models import User

#         user: User = get_current_user()  # type: ignore
#         user.delete()
#         return {"message": "user deleted"}


# app.add_url_rule("/user", view_func=UserView.as_view("user"))  # type: ignore
