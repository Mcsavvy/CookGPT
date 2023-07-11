import click

from cookgpt.user import app
from cookgpt.user.models import User


def create_user(fname, lname, email, username, password):
    """Creates user"""
    return User.create(
        first_name=fname,
        last_name=lname,
        email=email,
        username=username,
        password=password,
    )


@app.cli.command()
@click.option("--fname", "-f", required=True)
@click.option("--lname", "-l", required=True)
@click.option("--email", "-e", required=True)
@click.option("--username", "-u")
@click.option("--password", "-p", required=True)
def create(fname, lname, email, username, password):
    """Adds a new user to the database"""
    try:
        create_user(fname, lname, email, username, password)
    except Exception as err:
        click.echo(err, err=True)
        raise click.Abort()
