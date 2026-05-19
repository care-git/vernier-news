from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx

from app.pipeline.ingestion.normalise import NormalisedArticle

logger = logging.getLogger(__name__)

_BASE = "https://content.guardianapis.com/search"
_PAGE_SIZE = 50
_TIMEOUT = 20.0


async def fetch(outlet_id: int, api_key: str) -> list[NormalisedArticle]:
    """Fetch recent articles from the Guardian Content API."""
    params = {
        "api-key": api_key,
        "show-fields": "bodyText,byline",
        "page-size": _PAGE_SIZE,
        "order-by": "newest",
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.error("Guardian API error: %s", exc)
        return []

    articles = []
    for item in data.get("response", {}).get("results", []):
        fields = item.get("fields", {})
        body = fields.get("bodyText", "")
        try:
            published_at = datetime.fromisoformat(item["webPublicationDate"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            published_at = datetime.now(UTC)

        articles.append(
            NormalisedArticle(
                url=item.get("webUrl", ""),
                outlet_id=outlet_id,
                title=item.get("webTitle", ""),
                body=body,
                summary=body[:500],
                author=fields.get("byline") or None,
                language="en",
                published_at=published_at,
                collected_at=datetime.now(UTC),
                collection_source="api:guardian",
            )
        )

    logger.info("Guardian: fetched %d articles", len(articles))
    return [a for a in articles if a.url and a.title]
