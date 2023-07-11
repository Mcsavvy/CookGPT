from apiflask import APIBlueprint

app = APIBlueprint(
    "userview", __name__, url_prefix="/user", tag="user", cli_group="user"
)

import cookgpt.user.cli
