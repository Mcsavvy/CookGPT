from apiflask import APIBlueprint

from cookgpt import docs

app = APIBlueprint(
    "auth",
    __name__,
    url_prefix="/auth",
    cli_group="auth",
    tag={"name": "auth", "description": docs.AUTH},
)


from cookgpt.auth import cli  # noqa: E402, F401
from cookgpt.auth import views  # noqa: E402, F401
from cookgpt.auth.models import Token, User, UserInfo  # noqa: E402, F401
