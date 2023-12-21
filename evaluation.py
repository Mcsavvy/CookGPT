import pathlib
from time import sleep
from typing import Optional

import PIL.Image
import requests
from trulens_eval.feedback import Feedback, Groundedness
from trulens_eval.feedback.provider.litellm import LiteLLM
from trulens_eval.tru import Tru
from trulens_eval.tru_basic_app import TruBasicApp

from cookgpt.ext.genai import gemini, gemini_vision, genai, glm  # noqa: F401

# litellm.set_verbose = True

image_urls = [
    "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg",
    "https://img.freepik.com/free-photo/fresh-pasta-with-hearty-bolognese-parmesan-cheese-generated-by-ai_188544-9469.jpg",
]


provider = LiteLLM()
grounded = Groundedness(groundedness_provider=provider)

# LLM-based feedback functions
f_insensitivity = Feedback(
    provider.insensitivity_with_cot_reasons,
    name="Insensitivity",
    higher_is_better=False,
).on_output()

# Moderation feedback functions
f_hate = Feedback(
    provider.harmfulness_with_cot_reasons,
    name="Harmfulness",
    higher_is_better=False,
).on_output()

harmless_feedbacks = [
    f_insensitivity,
    f_hate,
]


def load_image(url: str) -> PIL.Image.Image:
    """
    Load an image from a URL.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()
    image = PIL.Image.open(response.raw)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    return image


def image_analysis(prompt: Optional[str]) -> str:
    """
    Analyze images using Gemini Vision.
    """
    print("Prompting Gemini Vision AI...")

    for image_url in image_urls:
        print(f"Analyzing image: {image_url}")
        try:
            image = load_image(image_url)
        except Exception as e:
            print(f"Failed to load image: {e}")
            continue
        contents = [image]
        if prompt:
            contents.insert(0, prompt)
        try:
            response = gemini_vision.generate_content(contents)
        except Exception as e:
            print(f"Failed to analyze image: {e}")
            return ""
        description = response.text
        print(f"> {description}")
        return description
        print("Waiting for 60 seconds...")
        sleep(60)


def run_image_analysis(app_id: str, prompt: Optional[str] = None):
    """
    Run the evaluation.
    """
    print(f"Running evaluation with app '{app_id}'")
    image_analysis_recorder = TruBasicApp(
        image_analysis, app_id=app_id, feedbacks=harmless_feedbacks
    )
    with image_analysis_recorder as recorder:  # noqa: F841
        image_analysis_recorder.app(prompt)


def main(tru: Tru):
    """
    Run the evaluation.
    """
    tru.start_dashboard(force=True, _dev=pathlib.Path.cwd().resolve())
    tru.reset_database()
    run_image_analysis(
        app_id="Simple Image Description", prompt="Describe this image:"
    )


if __name__ == "__main__":
    tru = Tru()  # noqa: F841
    try:
        main(tru)
    except KeyboardInterrupt:
        tru.stop_dashboard()
