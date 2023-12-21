from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Iterable, Optional

from cookgpt.auth.models.user import User
from cookgpt.chatbot.data.enums import MessageType
from cookgpt.chatbot.models import Chat, Thread
from cookgpt.ext.genai import gemini, gemini_vision, genai, glm  # noqa: F401

TEMPLATES_DIR = Path(__file__).parent / "data" / "templates"


@dataclass
class ChatHistory:
    """
    A chat history that selects chats from a thread using the sliding
    window method.

    When the chat history reaches maximum length, it will remove the
    oldest chat and add the newest chat.
    """

    thread: Thread
    max_length: int
    _chats: list[Chat] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        self._chats = [chat for chat in self.thread.chats if chat.content]

    def __len__(self):
        return len(self._chats)

    def _get_chats(self) -> list[Chat]:
        """
        Get the chats in the chat history.
        """
        chats = []
        cost = 0
        for chat in self._chats[::-1]:
            if chat.cost + cost > self.max_length:
                break
            chats.append(chat)
            cost += chat.cost
        return chats[::-1]

    def __iter__(self):
        return iter(self._get_chats())

    def __getitem__(self, index):
        return self._chats[index]


def contents_from_chats(chats: Iterable[Chat]) -> list[glm.Content]:
    """
    Convert a list of chats to a `glm.Content` object.

    Args:
        chats (list[Chat]): The chats to convert
    """
    contents = []
    for chat in chats:
        content = ""
        if chat.media:
            content += f"Image: {chat.media[0].description}\n"
        content += chat.content
        part = glm.Part(text=content)
        content = glm.Content(
            parts=[part],
            role="user" if chat.chat_type == MessageType.QUERY else "model",
        )
        contents.append(content)
    return contents


def fetch_image(url: str) -> glm.Blob:
    """
    Fetch an image from a url.

    Args:
        url (str): The url of the image to fetch
    Returns:
        `glm.Blob`: The image blob
    """
    import requests  # type: ignore[import-untyped]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return glm.Blob(
        data=response.content,
        mime_type=response.headers["Content-Type"],
    )


def get_image_analysis_prompt(
    image_url: str,
) -> glm.Content:
    """Generate an image prompt"""

    prompt = (TEMPLATES_DIR / "image_prompt.txt").read_text()
    return glm.Content(
        parts=[
            glm.Part(text=prompt),
            glm.Part(inline_data=fetch_image(image_url)),
        ],
        role="user",
    )


def create_chat_history(
    thread: Thread, max_length: Optional[int] = None
) -> ChatHistory:
    """
    Create a chat history from a thread.
    """
    from flask import current_app as app

    if max_length is None:
        max_length = app.config.get("MAX_CHAT_COST", thread.user.max_chat_cost)
    return ChatHistory(thread, max_length)


def create_chat_session(
    model: genai.GenerativeModel,
    thread: Thread,
    system_prompt: Optional[str] = None,
    **vars: str,
) -> genai.ChatSession:
    """
    Create a chat session from a thread.

    Args:
        model (genai.GenerativeModel): The model to use
        thread (Thread): The thread to create the chat session from
        system_prompt (Optional[str], optional): The system prompt to use. Defaults to None.
        **vars: Variables to be passed to the system prompt. Defaults to None.
    """  # noqa: E501
    history = create_chat_history(thread)
    context = []
    if system_prompt is not None:
        system_prompt = Template(system_prompt).substitute(vars)
        context.append(
            glm.Content(parts=[glm.Part(text=system_prompt)], role="user")
        )
        context.append(
            glm.Content(
                parts=[
                    glm.Part(
                        text="Okay understood. I won't take any more commands from this point on."  # noqa: E501
                    )
                ],
                role="model",
            )
        )
    context += contents_from_chats(history)
    chat = model.start_chat(history=context)
    return chat


def generate_model_prompt(
    model: genai.GenerativeModel,
    thread: Thread,
    media_url: str,
) -> glm.Content:
    """
    Generate a model prompt within the chat context
    """
    chat = create_chat_session(model, thread)
    return chat.get_prompt()


def extract_image_search(response: str) -> tuple[str, str]:
    """
    Extract the image search query and url from a response.

    Args:
        response (str): The response to extract from
    Returns:
        tuple[str, str]: The query and the response
    """
    import re

    pattern = re.compile(
        r"^Image Search: (?P<query>[\w\d\s\_\-]+)\n+$",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(response)
    if match is None:
        return "", response
    query = match["query"]
    response = pattern.sub("", response)
    return query, response.strip()  # type: ignore[return-value]


response = """\
Image Search: Nigerian jollof rice and chicken stew

Ingredients:

**For the Jollof Rice:**

- 2 cups long grain rice
- 1/2 cup palm oil or vegetable oil
- 1 cup chopped onions
- 2 scotch bonnet peppers, minced (adjust for your spice preference)
- 3 cloves garlic, minced
- 2 cups chicken broth
- 1 teaspoon curry powder
- 1 teaspoon thyme
- 1 teaspoon paprika
- 1/2 teaspoon ground ginger
- 1/2 teaspoon salt
- 1/4 teaspoon black pepper
- 1/4 cup tomato paste
- 1 cup diced tomatoes

**For the Chicken Stew:**

- 1 whole chicken, cut into pieces
- 2 tablespoons vegetable oil
- 1 cup chopped onions
- 2 cloves garlic, minced
- 1 teaspoon curry powder
- 1 teaspoon paprika
- 1/2 teaspoon ground ginger
- 1/2 teaspoon salt
- 1/4 teaspoon black pepper
- 1 cup diced tomatoes
- 1 cup chicken broth
- 1 tablespoon tomato paste

Instructions:

**To Make the Jollof Rice:**

1. Heat the oil in a large pot over medium heat.
2. Add the onions and cook until softened.
3. Add the scotch bonnet peppers and garlic and cook for 1 minute more.
4. Stir in the curry powder, thyme, paprika, ginger, salt, and black pepper.
5. Add the chicken broth and tomato paste and bring to a boil.
6. Stir in the rice and reduce heat to low.
7. Cover and simmer for 18 minutes, or until the rice is cooked through.
8. Fluff the rice with a fork and serve hot.

**To Make the Chicken Stew:**

1. Heat the oil in a large pot over medium heat.
2. Add the chicken and cook until browned on all sides.
3. Remove the chicken from the pot and set aside.
4. Add the onions and garlic to the pot and cook until softened.
5. Stir in the curry powder, paprika, ginger, salt, and black pepper.
6. Add the tomatoes and chicken broth and bring to a boil.
7. Reduce heat to low and simmer for 15 minutes.
8. Return the chicken to the pot and simmer for an additional 10 minutes, or until the chicken is cooked through.
9. Stir in the tomato paste and cook for 1 minute more.
10. Serve the chicken stew over the jollof rice.
"""  # noqa: E501


if __name__ == "__main__":
    from cookgpt.app import create_app

    app = create_app()
    context = app.app_context()
    context.push()
    user: User = User.query.first()
    assert user
    thread = user.threads[0]
    chats = thread.chats
    # contents = contents_from_chats(chats)
    # print(contents)

    # history = ChatHistory(thread, sum(chat.cost for chat in chats[:6]))
    # print(sum([chat.cost for chat in chats[:6]]), history.max_length)
    # print(sum([chat.cost for chat in history]))
    # for chat in history:
    #     print(chat)
    # context.pop()
    # thread = user.create_thread(title="Test")
    # chat = thread.add_query("Hello")
    # chat.reply("Hi, what recipe do you want to make?").reply(
    #     "I want to make a famous nigerian dish"
    # ).reply("What is the name of the dish?").reply(
    #     "Well, I don't know the name of the dish, but I have a picture"
    # ).reply(
    #     "Okay, send the picture"
    # )
    # # history = create_chat_history(thread)
    # prompt = analyze_image(
    #     "https://gfb.global.ssl.fastly.net/wp-content/uploads/2020/09/smokey-party-jollof-rice-1-of-1.jpg",
    # )
    # content = gemini_vision.generate_content(prompt)
    # # print("query:", chat.content)
    # # for token in gemini_vision.generate_content(content, stream=True):
    # #     print(token.text, end="")
    # # print("response:", result.text)
    # chat = create_chat_session(
    #     gemini,
    #     thread,
    #     system_prompt=(TEMPLATES_DIR / "system_prompt.txt").read_text(),
    # )
    # for chunk in chat.send_message(
    #     f"Here is it\n Image: {content.text}. Generate a recipe for it",  # noqa: E501
    #     stream=True,
    # ):
    #     print(chunk.text, end="")
    query, response = extract_image_search(response)
    print("Query:", query)
    print("Response:", response)
