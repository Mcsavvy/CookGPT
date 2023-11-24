from cookgpt.socketchef.app import Namespace


class ChatNamespace(Namespace):
    """Chat namespace."""

    def on_connect(self):
        """Handle a connection."""
        from cookgpt.socketchef.app import request

        super().on_connect()
        self.enter_room(request.sid, self.current_user.id.hex)

    def on_disconnect(self):
        """Handle a disconnection."""
        from flask import request

        self.leave_room(request.sid, self.current_user.id.hex)
        super().on_disconnect()


from cookgpt.socketchef.chat.query import *  # noqa: F401, F403, E402
