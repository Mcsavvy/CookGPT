from typing import Optional
from uuid import UUID

from cookgpt.chatbot.message import get_image_analysis_prompt
from cookgpt.chatbot.models import ChatMedia
from cookgpt.chatbot.utils import get_stream_name
from cookgpt.ext.genai import gemini_vision
from cookgpt.utils import utcnow
from redisflow import celeryapp as app


@app.task(name="chatbot.fetch_image_description")
def fetch_image_description(chatmedia_id: UUID):
    """fetch image description from ai"""

    chatmedia = ChatMedia.query.get(chatmedia_id)
    assert chatmedia, "Chat media does not exist"

    prompt = get_image_analysis_prompt(chatmedia.url)
    response = gemini_vision.generate_content(prompt)
    description = response.text
    chatmedia.update(description=description)
    return description


@app.task(name="chatbot.send_query")
def send_query(
    query_id: UUID,
    response_id: UUID,
    thread_id: UUID,
    user_query: str,
    image_desc: Optional[str] = None,
):
    """send query to ai and process response"""

    from cookgpt.chatbot.message import TEMPLATES_DIR, create_chat_session
    from cookgpt.chatbot.models import Chat, Thread
    from cookgpt.ext.database import db
    from cookgpt.ext.genai import gemini
    from cookgpt.globals import current_app as app

    query = db.session.get(Chat, query_id)
    assert query, "Query for task does not exist"

    response = db.session.get(Chat, response_id)
    assert response, "Response for task does not exist"

    thread = db.session.get(Thread, thread_id) or response.thread
    assert thread, "Thread for task does not exist"

    # create chat session
    chat = create_chat_session(
        thread=thread,
        model=gemini,
        system_prompt=(TEMPLATES_DIR / "system_prompt.txt").read_text(),
        user=thread.user.name,
    )

    stream = get_stream_name(thread.user, response)
    app.redis.set(f"{stream}:task", "STARTED")

    # Add image description to prompt if available
    if image_desc:
        prompt = f"Image: {image_desc}\n{user_query}"
    else:
        prompt = user_query

    prompt = prompt.strip()

    # calculate cost and time
    query_cost = len(prompt) / 4
    query_time = utcnow()
    response_cost = 0
    ai_response = ""

    # send prompt to ai in chunks
    for chunk in chat.send_message(prompt):
        # add to redis stream
        app.redis.xadd(
            stream,
            {"token": chunk.text, "count": 1, "chunk": chunk.text},
            maxlen=1000,
        )
        # add to response and cost
        ai_response += chunk.text
        response_cost += len(chunk.text)

    # update query and response
    response_time = utcnow()
    query.update(
        content=user_query,
        cost=query_cost,
        sent_time=query_time,
    )
    response.update(
        content=ai_response,
        cost=response_cost,
        sent_time=response_time,
    )
    app.redis.set(f"{stream}:task", "COMPLETED")
