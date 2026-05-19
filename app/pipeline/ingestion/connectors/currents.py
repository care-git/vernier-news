from __future__ import annotations

import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from app.pipeline.ingestion.normalise import NormalisedArticle

logger = logging.getLogger(__name__)

_BASE = "https://api.currentsapi.services/v1/latest-news"
_TIMEOUT = 20.0


async def fetch(outlet_map: dict[str, int], api_key: str) -> list[NormalisedArticle]:
    """Fetch latest news from the Currents API, attributing each to its source outlet."""
    params = {"apiKey": api_key, "language": "en"}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.error("Currents API error: %s", exc)
        return []

    articles = []
    for item in data.get("news", []):
        url = item.get("url", "")
        domain = urlparse(url).netloc.removeprefix("www.")
        outlet_id = outlet_map.get(domain)
        if outlet_id is None:
            continue

        try:
            published_at = datetime.fromisoformat(item.get("published", ""))
        except ValueError:
            published_at = datetime.now(timezone.utc)

        body = item.get("description", "")
        articles.append(NormalisedArticle(
            url=url,
            outlet_id=outlet_id,
            title=item.get("title", ""),
            body=body,
            summary=body[:500],
            author=item.get("author") or None,
            language=item.get("language", "en"),
            published_at=published_at,
            collected_at=datetime.now(timezone.utc),
            collection_source="api:currents",
        ))

    logger.info("Currents: fetched %d articles (from %d total)", len(articles), len(data.get("news", [])))
    return [a for a in articles if a.url and a.title]
