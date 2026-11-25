
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl


MediaType = Literal[
    "image",
    "video",
    "audio",
    "text",
    "code",
    "watermark",
]


class DetectionRequest(BaseModel):
    mediaType: MediaType

    content: str | None = None
    url: HttpUrl | None = None

    languageHint: str | None = None

