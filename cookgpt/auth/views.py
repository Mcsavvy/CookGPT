"""Views for authentication."""

from typing import Any, cast
from uuid import UUID

from apiflask.views import MethodView

# from apiflask.views import MethodView
from flask_jwt_extended import get_current_user, get_jwt

from cookgpt import docs, logging
from cookgpt.auth import app
from cookgpt.auth.data import examples as ex
from cookgpt.auth.data import schemas as sc
from cookgpt.auth.data import validators as v
from cookgpt.auth.data.enums import UserType
from cookgpt.auth.models import Token
from cookgpt.ext.auth import auth_required
from cookgpt.ext.database import db
from cookgpt.utils import abort, api_output


@app.post("/login")
@app.input(sc.Auth.Login.Body, example=ex.Auth.Login.Body)
@app.output(
    sc.Auth.Login.Response,
    200,
    example=ex.Auth.Login.Response,
    description="Authentication info",
)
@api_output(
    sc.Auth.Login.NotFound,
    404,
    example=ex.Auth.Login.NotFound,
    description="Error message if user does not exist",
)
@api_output(
    sc.Auth.Login.Unauthorized,
    401,
    example=ex.Auth.Login.Unauthorized,
    description="Error message if password is incorrect",
)
@app.doc(description=docs.AUTH_LOGIN)
def login(json_data: dict) -> Any:
    """Log a user into the system."""
    from cookgpt.auth.models import User

    login: str = json_data["login"]
    password: str = json_data["password"]
    user: User | None

    logging.info("Attempting to log in user: %s", login)
    if "@" in login:
        user = User.query.filter(User.email == login).first()
    else:
        user = User.query.filter(User.username == login).first()
    if user is None:
        logging.debug("User does not exist: %s", login)
        abort(404, "User does not exist")
    elif not user.validate_password(password):
        logging.debug("Incorrect password for user: %s", login)
        abort(401, "Cannot authenticate")
    token: "Token" = user.request_token()
    return {
        "message": "Successfully logged in",
        "auth_info": {
            "user_id": user.id,
            "user_name": user.name,
            "atoken": token.access_token,
            "atoken_expiry": token.atoken_expiry,
            "rtoken": token.refresh_token,
            "rtoken_expiry": token.rtoken_expiry,
            "user_type": user.type,
            "auth_type": "Bearer",
        },
    }


@app.post("/logout")
@auth_required()
@app.output(
    sc.Auth.Logout.Response,
    200,
    example=ex.Auth.Logout.Response,
    description="Success message",
)
@app.doc(description=docs.AUTH_LOGOUT)
def logout() -> Any:
    """Log a user out of the system."""
    from cookgpt.auth.models import User

    logging.info("Logging out user...")
    jwt = get_jwt()
    user: "User" = get_current_user()
    token = db.session.get(Token, UUID(jwt["jti"]))
    assert token is not None
    logging.debug("Deactivating token: %s", token)
    user.deactivate_token(token)
    return {"message": "Logged out user"}


@app.post("/signup")
@app.input(sc.Auth.Signup.Body, example=ex.Auth.Signup.Body)
@app.output(
    sc.Auth.Signup.Response,
    201,
    example=ex.Auth.Signup.Response,
    description="Success message",
)
@api_output(
    sc.Auth.Signup.Error,
    422,
    example=ex.Auth.Signup.Error,
    description="Error message while creating user",
)
@app.doc(description=docs.AUTH_SIGNUP)
def signup(json_data: dict) -> Any:
    """Signup a new user."""
    from cookgpt.auth.models import User

    logging.info("Signing up user...")
    name: str = json_data.pop("first_name")
    first_name, last_name = v.FirstNameOrFullName()(name)
    logging.debug("First name: %s", first_name)
    json_data["first_name"] = first_name
    if last_name is not None:
        logging.debug("Last name: %s", last_name)
        json_data["last_name"] = last_name
    try:
        User.create(**json_data, user_type=UserType.COOK)
    except User.CreateError as err:
        logging.debug("Error while creating user: %s", err.args[0])
        return {"message": err.args[0]}, 422
    return {"message": "Successfully signed up"}, 201


@app.post("/refresh")
@auth_required(refresh=True)
@app.output(
    sc.Auth.Refresh.Response,
    200,
    example=ex.Auth.Refresh.Response,
    description="Authentication info",
)
@app.doc(description=docs.AUTH_REFRESH)
def refresh() -> Any:
    """Refresh the access token."""
    logging.info("Refreshing access token...")
    jti = UUID(get_jwt()["jti"])
    token = cast(Token, db.session.get(Token, jti))
    token.refresh()
    return {
        "message": "Refreshed access token",
        "auth_info": {
            "user_id": token.user.id,
            "user_name": token.user.name,
            "atoken": token.access_token,
            "atoken_expiry": token.atoken_expiry,
            "rtoken": token.refresh_token,
            "rtoken_expiry": token.rtoken_expiry,
            "user_type": token.user.type,
            "auth_type": "Bearer",
        },
    }


class UserView(MethodView):
    """User view."""

    decorators = [auth_required()]

    @app.output(
        sc.User.Info.Response,
        description="User information",
        example=ex.User.Info.Response,
    )
    @app.doc(tags=["user"], description=docs.USER_INFO)
    def get(self):
        """Get user's information."""
        user = get_current_user()
        user.user_type = user.type
        return user

    @app.input(sc.User.Update.Body, example=ex.User.Update.Body)
    @app.output(
        sc.User.Update.Response,
        description="Success message after modifying user info",
        example=ex.User.Update.Response,
    )
    @api_output(
        sc.User.Update.Error,
        422,
        "Error while updating user",
        example=ex.User.Update.Error,
    )
    @app.doc(tags=["user"], description=docs.USER_UPDATE)
    def patch(self, json_data):
        """Update user's information."""
        from cookgpt.auth.models import User

        user: User = get_current_user()  # type: ignore
        try:
            updated = user.update(**json_data)
        except User.UpdateError as err:
            abort(422, err.args[0])
        if not updated:  # pragma: no cover
            {"message": "No changes made"}
        return {"message": "Successfully updated user"}

    @app.output(
        sc.User.Delete.Response,
        description="Success message after deletion of user",
        example=ex.User.Delete.Response,
    )
    @api_output(
        sc.User.Delete.Error,
        422,
        "Error while deleting user",
        example=ex.User.Delete.Error,
    )
    @app.doc(tags=["user"], description=docs.USER_DELETE)
    def delete(self):
        """Delete a user."""
        abort(422, "Cannot delete user")


app.add_url_rule("/user", view_func=UserView.as_view("user"))  # type: ignore
