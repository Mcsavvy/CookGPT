"""Auth blueprint."""

from apiflask import APIBlueprint

from cookgpt import docs

app = APIBlueprint(
    "auth",
    __name__,
    url_prefix="/auth",
    cli_group="auth",
    tag={"name": "auth", "description": docs.AUTH},
)


from cookgpt.auth import cli, views  # noqa: E402, F401, I001
from cookgpt.auth.models import Token, User  # noqa: E402, F401, I001
