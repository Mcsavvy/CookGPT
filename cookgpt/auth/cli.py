from typing import Literal

import click
from marshmallow.utils import INCLUDE

from cookgpt.auth import app
from cookgpt.auth.data.enums import UserType
from cookgpt.auth.data.schemas import UserCreate
from cookgpt.auth.models import User


@app.cli.command("create-user")
@click.option("--fname", "-f", required=True, help="first name of the admin")
@click.option("--lname", "-l", required=True, help="last name of the admin")
@click.option("--email", "-e", required=True, help="admin's email")
@click.option("--password", "-p", required=True, help="admin's password")
@click.option("--username", "-u", help="admin's username")
@click.option(
    "--allow-existing",
    "-a",
    is_flag=True,
    default=True,
    help="don't raise an error is admin already exists",
)
@click.option(
    "--user-type",
    "-t",
    type=click.Choice(["ADMIN", "COOK"], False),
)
def create_user(
    fname: str,
    lname: str,
    email: str,
    password: str,
    username: str,
    allow_existing: bool,
    user_type: Literal["ADMIN", "COOK"],
):
    """Create a new user"""
    user = None
    if username:
        user = User.query.filter(
            (User.username == username) & (User.email == email)
        ).first()
    if not user and username:
        user = User.query.filter(User.username == username).first()
    if not user:
        user = User.query.filter(User.email == email).first()
    if user is not None:
        if email == user.email and (username and user.username == username):
            click.echo(
                (
                    f"{user.user_type.value.title()} user "
                    "with that username and email already exists"
                )
            )
        elif email == user.email:
            click.echo(
                (
                    f"{user.user_type.value.title()} user "
                    "with that email already exists"
                )
            )
        else:
            click.echo(
                (
                    f"{user.user_type.value.title()} user "
                    "with that username already exists"
                )
            )
        if allow_existing:
            return
        raise click.Abort()

    payload = {
        "first_name": fname,
        "last_name": lname,
        "username": username,
        "password": password,
        "email": email,
        "user_type": UserType(user_type.lower()),
    }
    if username is None:  # pragma: no cover
        del payload["username"]
    cleaned: dict = UserCreate.In().load(  # type: ignore
        payload, unknown=INCLUDE
    )
    new_user = User.create(**cleaned)
    print(f"Created {user_type.lower()} '{fname}' with id {new_user.id!s}")


@app.cli.command("create-admin")
@click.option("--fname", "-f", required=True, help="first name of the admin")
@click.option("--lname", "-l", required=True, help="last name of the admin")
@click.option("--email", "-e", required=True, help="admin's email")
@click.option("--password", "-p", required=True, help="admin's password")
@click.option("--username", "-u", help="admin's username")
@click.option(
    "--allow-existing",
    "-a",
    is_flag=True,
    flag_value=True,
    help="don't raise an error is admin already exists",
)
def create_admin(fname, lname, email, password, username, allow_existing):
    """Create an administrative user"""
    create_user.callback(
        fname=fname,
        lname=lname,
        email=email,
        password=password,
        username=username,
        allow_existing=allow_existing,
        user_type="ADMIN",
    )  # type: ignore


@app.cli.command("create-cook")
@click.option("--fname", "-f", required=True, help="first name of the cook")
@click.option("--lname", "-l", required=True, help="last name of the cook")
@click.option("--email", "-e", required=True, help="cook's email")
@click.option("--password", "-p", required=True, help="cook's password")
@click.option("--username", "-u", help="cook's username")
@click.option(
    "--allow-existing",
    "-a",
    is_flag=True,
    flag_value=True,
    help="don't raise an error if cook already exists",
)
def create_cook(fname, lname, email, password, username, allow_existing):
    """Create a cook"""
    create_user.callback(
        fname=fname,
        lname=lname,
        email=email,
        password=password,
        username=username,
        allow_existing=allow_existing,
        user_type="COOK",
    )  # type: ignore


@app.cli.command("get-access-token")
@click.argument("identity")
@click.option(
    "--new", "-n", is_flag=True, default=False, help="create a new token"
)
def get_access_token(identity: str, new: bool) -> None:
    user: "User"

    user = User.query.filter(
        (User.email == identity) | (User.username == identity)
    ).first()
    if user is None:
        raise click.Abort("User not found")
    if new:
        token = user.create_token()
    else:
        token = user.request_token()
    click.echo(f"Access token: {token.access_token}")
