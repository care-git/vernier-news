from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NormalisedArticle:
    url: str
    outlet_id: int
    title: str
    body: str
    summary: str
    author: str | None
    language: str
    published_at: datetime
    collected_at: datetime
    collection_source: str
    raw_html: str = ""
    extra: dict = field(default_factory=dict)


def normalise(raw: dict, outlet_id: int, collection_source: str) -> NormalisedArticle | None:
    """Strip HTML, normalise encoding, detect language, and return a NormalisedArticle.

    Returns None if the raw item lacks the minimum required fields (url, title).
    """
    ...
