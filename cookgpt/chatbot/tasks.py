"""chatbot tasks."""

from typing import Any
from uuid import UUID

from redisflow import celeryapp as app


@app.task(name="chatbot.send_query")
def send_query(
    query_id: UUID,
    response_id: UUID,
    thread_id: UUID,
    kwargs: "dict[str, Any]",
):
    """Send query to ai and process response."""
    from cookgpt import logging
    from cookgpt.chatbot.callback import ChatCallbackHandler
    from cookgpt.chatbot.chain import ThreadChain
    from cookgpt.chatbot.models import Chat, Thread
    from cookgpt.chatbot.utils import get_stream_name, use_chat_callback
    from cookgpt.ext.database import db
    from cookgpt.globals import current_app as app
    from cookgpt.globals import resetvar, setvar

    logging.info("Sending query to AI using celery")

    chain = ThreadChain()

    query = db.session.get(Chat, query_id)
    assert query, "Query for task does not exist"

    response = db.session.get(Chat, response_id)
    assert response, "Response for task does not exist"

    thread = db.session.get(Thread, thread_id) or response.thread
    assert thread, "Thread for task does not exist"

    stream = get_stream_name(thread.user, response)
    app.redis.set(f"{stream}:status", "STARTED")

    setvar("thread", thread)
    setvar("chain", chain)
    setvar("query", query)
    setvar("response", response)
    setvar("user", thread.user)

    with use_chat_callback(ChatCallbackHandler()):
        chain.predict(**kwargs)

    logging.info(f"Adding stream {stream!r} to completed streams")
    logging.debug(f"redis: {app.redis}")
    # FIXME: redis has been unset
    app.redis.set(f"{stream}:status", "COMPLETED")
    app.redis.lpush("streams:completed", stream)

    resetvar("thread")
    resetvar("chain")
    resetvar("query")
    resetvar("response")
    resetvar("user")
