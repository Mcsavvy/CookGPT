"""
utilize google image search to find images
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional, TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT")


class ImageResult(BaseModel):
    """Result from google image search"""

    title: str
    """title of the image"""

    imageUrl: str
    """url of the image"""

    imageWidth: int
    """width of the image"""

    imageHeight: int
    """height of the image"""

    thumbnailUrl: str
    """url of the thumbnail"""

    thumbnailWidth: int
    """width of the thumbnail"""

    thumbnailHeight: int
    """height of the thumbnail"""

    source: str
    """source of the image"""

    domain: str
    """domain of the image"""

    link: str
    """link to the image"""

    googleUrl: str
    """google url of the image"""

    position: int
    """position of the image"""


def _get_serper_api_key():
    from cookgpt.ext.config import config

    try:
        return config.SERPER_API_KEY
    except (KeyError, AttributeError):
        raise ValueError(
            "You must set the SERPER_API_KEY config to use this feature."
        )


@dataclass
class Serper:
    """Serper Wrapper"""

    type: Literal[
        "images", "news", "videos", "shopping", "places", "search"
    ] = "images"
    """type of search"""

    api_key: str = field(
        init=False,
        repr=False,
        compare=False,
        default_factory=_get_serper_api_key,
    )
    """serper.dev api key"""

    country: Optional[str] = None
    """country to search from"""

    locale: Optional[str] = None
    """language to search in"""

    auto_correct: bool = False
    """whether to auto correct the query"""

    page: int = 1
    """used for pagination"""

    num: int = 10
    """number of results to return"""

    @property
    def url(self) -> str:
        """url to query"""
        return "https://google.serper.dev/" + self.type

    def _construct_payload(self) -> dict[str, str]:
        """construct payload for request"""
        payload: dict[str, Any] = {}
        if not self.auto_correct:
            payload["autocorrect"] = False
        if self.num > 10:
            payload["num"] = self.num
        if self.country and self.country.lower() != "us":
            payload["gl"] = self.country.lower()
        if self.locale and self.locale.lower() != "en":
            payload["hl"] = self.locale.lower()
        if self.page > 1:
            payload["page"] = self.page
        return payload

    def _get_headers(self) -> dict[str, str]:
        """get headers for request"""
        return {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

    def search(
        self, query: str, model: Callable[..., ModelT] = lambda x: x
    ) -> list[ModelT]:
        """fetch results from serper.dev"""
        import requests

        payload = self._construct_payload()
        payload["q"] = query

        response = requests.post(
            self.url,
            json=payload,
            headers=self._get_headers(),
        )
        # print(payload)
        # print(response.request.headers)
        response.raise_for_status()
        return [model(**result) for result in response.json()[self.type]]


if __name__ == "__main__":
    image_search = Serper(
        type="images",
        auto_correct=True,
    )
    results = image_search.search(
        "Nigerian jollof rice and chicken stew", ImageResult
    )
    print(results[:2])
