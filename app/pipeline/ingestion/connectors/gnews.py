from __future__ import annotations

import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from app.pipeline.ingestion.normalise import NormalisedArticle

logger = logging.getLogger(__name__)

_BASE = "https://gnews.io/api/v4/top-headlines"
_TIMEOUT = 20.0


async def fetch(outlet_map: dict[str, int], api_key: str) -> list[NormalisedArticle]:
    """Fetch top headlines from the GNews API, attributing each to its source outlet."""
    params = {"apikey": api_key, "lang": "en", "max": 10}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.error("GNews API error: %s", exc)
        return []

    articles = []
    for item in data.get("articles", []):
        url = item.get("url", "")
        domain = urlparse(url).netloc.removeprefix("www.")
        outlet_id = outlet_map.get(domain)
        if outlet_id is None:
            continue

        try:
            published_at = datetime.fromisoformat(
                item.get("publishedAt", "").replace("Z", "+00:00")
            )
        except ValueError:
            published_at = datetime.now(timezone.utc)

        body = item.get("content", "") or item.get("description", "")
        articles.append(NormalisedArticle(
            url=url,
            outlet_id=outlet_id,
            title=item.get("title", ""),
            body=body,
            summary=item.get("description", "")[:500],
            author=None,
            language="en",
            published_at=published_at,
            collected_at=datetime.now(timezone.utc),
            collection_source="api:gnews",
        ))

    logger.info("GNews: fetched %d articles (from %d total)", len(articles), len(data.get("articles", [])))
    return [a for a in articles if a.url and a.title]
