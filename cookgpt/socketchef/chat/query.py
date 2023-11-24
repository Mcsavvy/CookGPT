from uuid import UUID

from cookgpt import logging
from cookgpt.chatbot.callback import ChatCallbackHandler
from cookgpt.chatbot.chain import ThreadChain
from cookgpt.chatbot.memory import get_memory_input_key
from cookgpt.chatbot.models import Chat, Thread
from cookgpt.chatbot.utils import get_thread, use_chat_callback
from cookgpt.ext.database import db
from cookgpt.globals import resetvar, setvar
from cookgpt.socketchef.app import namespace, socketio
from cookgpt.socketchef.namespaces import ChatNamespace as ns
from cookgpt.socketchef.validator import validate


def send_query(
    query_id: "UUID",
    response_id: "UUID",
    **kwargs,
):
    """send query to ai and process response"""

    logging.info("Sending query to AI in foreground")

    chain = ThreadChain()
    query = db.session.get(Chat, query_id)
    assert query, "Query does not exist"
    response = db.session.get(Chat, response_id)
    assert response, "Response does not exist"
    thread: "Thread" = query.thread

    logging.debug(f"Thread: {thread}")
    logging.debug(f"Query: {query}")
    logging.debug(f"Response: {response}")
    logging.debug(f"Chain: {chain}")

    setvar("thread", thread)
    setvar("chain", chain)
    setvar("query", query)
    setvar("response", response)
    setvar("user", thread.user)

    with use_chat_callback(ChatCallbackHandler()):
        chain.predict(**kwargs)

    resetvar("thread")
    resetvar("chain")
    resetvar("query")
    resetvar("response")
    resetvar("user")


@ns.on("query")
@socketio.auth_required
def on_query(data):
    """Send a query to the AI."""

    logging.info("Received query from client")
    thread_id = data.get("thread_id")
    user = namespace.current_user
    input_key = get_memory_input_key()
    query: str = data.get("query")

    assert query, "Query is empty"
    assert user, "User is not authenticated"

    if thread_id:
        thread = get_thread(thread_id, required=False)
        namespace.emit(
            "error",
            {
                "details": "The thread you are trying to access does not exist.",
                "data": {"thread_id": thread_id},
            },
        )
        logging.error("Thread does not exist")
        return
    else:
        thread = user.create_thread(title="New Thread")
        namespace.emit(
            "new_thread",
            {"id": str(thread.id), "title": thread.title},
            room=user.id.hex,
        )

    if thread.cost >= user.max_chat_cost:
        namespace.emit(
            "alert",
            {
                "title": "Not enough tokens",
                "level": "warning",
                "body": (
                    "You don't have enough tokens to make this request. ",
                    "Open a new thread to continue.",
                ),
            },
        )
        return
    q = thread.add_query(query)
    namespace.emit(
        "chat",
        {
            "chat_id": q.pk,
            "thread_id": thread.pk,
            "type": "query",
            "content": q.content,
        },
        room=user.id.hex,
        include_self=False,
    )
    r = thread.add_response("", previous_chat=q)

    send_query(q.id, r.id, **{input_key: query})
    namespace.emit(
        "chat",
        {
            "chat_id": r.pk,
            "thread_id": thread.pk,
            "content": r.content,
            "type": "response",
        },
        room=user.id.hex,
        include_self=True,
    )


@validate
def foo(bar: str, baz: int = 42):
    """Foo bar baz."""
    print(bar, baz)
