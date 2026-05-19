from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from bs4 import BeautifulSoup
from langdetect import LangDetectException, detect


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


def _strip_html(html: str) -> str:
    if not html:
        return ""
    return BeautifulSoup(html, "lxml").get_text(separator=" ", strip=True)


def _parse_date(entry: dict) -> datetime:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        val = entry.get(key)
        if val:
            try:
                return datetime(*val[:6], tzinfo=UTC)
            except (TypeError, ValueError):
                continue
    return datetime.now(UTC)


def _detect_language(text: str) -> str:
    try:
        return detect(text[:300])
    except LangDetectException:
        return "unknown"


def normalise(raw: dict, outlet_id: int, collection_source: str) -> NormalisedArticle | None:
    """Strip HTML, normalise encoding, detect language, and return a NormalisedArticle.

    Returns None if the raw item lacks the minimum required fields (url, title).
    """
    url = (raw.get("link") or raw.get("url") or "").strip()
    title = (raw.get("title") or "").strip()

    if not url or not title:
        return None

    # Prefer full content over summary when available
    content_list = raw.get("content") or []
    raw_html = content_list[0].get("value", "") if content_list else ""
    body_html = raw_html or raw.get("summary", "")

    body = _strip_html(body_html)
    summary = _strip_html(raw.get("summary", ""))[:500]
    author = (raw.get("author") or "").strip() or None
    published_at = _parse_date(raw)

    language = _detect_language(f"{title} {body[:200]}")

    return NormalisedArticle(
        url=url,
        outlet_id=outlet_id,
        title=title,
        body=body,
        summary=summary,
        author=author,
        language=language,
        published_at=published_at,
        collected_at=datetime.now(UTC),
        collection_source=collection_source,
        raw_html=raw_html,
    )
