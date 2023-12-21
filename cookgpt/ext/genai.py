from typing import TYPE_CHECKING

import google.ai.generativelanguage as glm  # noqa: F401
import google.generativeai as genai

gemini = genai.GenerativeModel(model_name="gemini-pro")
gemini_vision = genai.GenerativeModel(model_name="gemini-pro-vision")


if TYPE_CHECKING:
    from cookgpt.app import App


def init_app(app: "App"):
    """Initialize the Google Generative AI extension."""
    genai.configure(transport=app.config.get("GENAI_TRANSPORT", "rest"))
    return genai
