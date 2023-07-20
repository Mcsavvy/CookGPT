from uuid import UUID

from flask import jsonify
from flask_jwt_extended import (
    get_current_user,
    get_jwt,
    jwt_required,
    set_access_cookies,
    unset_access_cookies,
)

from cookgpt.auth import app
from cookgpt.auth.models import JwtToken

from .schemas import LoginSchema, SignupSchema


@app.post("/login")
@app.input(LoginSchema)
def login(data):
    """Login"""
    from cookgpt.user import User

    login = data["login"]
    password = data["password"]

    if "@" in login:
        user: "User" = User.query.filter_by(email=login).first()
    else:
        user: "User" = User.query.filter_by(username=login).first()
    if user is None:
        return {"message": "User does not exist"}, 404
    elif not user.validate_password(password):
        return {"message": "Cannot authenticate"}, 401
    access_token = user.request_jwt_token().access_token.encode()
    response = jsonify({"message": "Successfully logged in"})
    set_access_cookies(response, access_token)
    return response


@app.post("/logout")
@jwt_required()
def logout():
    """Logout"""
    from cookgpt.user.models import User

    jwt = get_jwt()
    user: "User" = get_current_user()
    token: "JwtToken" = JwtToken.query.get(UUID(jwt["jti"]))
    user.deactivate_jwt_token(token)
    response = jsonify({"message": "Successfully logged out"})
    unset_access_cookies(response)
    return response


@app.post("/signup")
@app.input(SignupSchema)
def signup(data):
    """Signup"""
    from cookgpt.user import User

    try:
        User.create(**data)
    except User.CreateError as err:
        return {"message": err.args[0]}, 422
    return {"message": "Successfully signed up"}, 201
