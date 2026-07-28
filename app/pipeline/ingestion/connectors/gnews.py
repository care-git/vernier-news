from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.pipeline.ingestion.normalise import NormalisedArticle, domain_from_url
from app.pipeline.ingestion.outlets import resolve_outlet

logger = logging.getLogger(__name__)

_BASE = "https://gnews.io/api/v4/top-headlines"
_TIMEOUT = 20.0


async def fetch(db: AsyncSession, api_key: str) -> list[NormalisedArticle]:
    """Fetch top headlines from the GNews API, attributing each to its source outlet.

    Outlets are created on discovery rather than matched against a seeded list — see
    app/pipeline/ingestion/outlets.py.
    """
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
        source = item.get("source") or {}
        outlet_id = await resolve_outlet(domain_from_url(url), db, name=source.get("name"))
        if outlet_id is None:
            continue

        try:
            published_at = datetime.fromisoformat(
                item.get("publishedAt", "").replace("Z", "+00:00")
            )
        except ValueError:
            published_at = datetime.now(UTC)

        body = item.get("content", "") or item.get("description", "")
        articles.append(
            NormalisedArticle(
                url=url,
                outlet_id=outlet_id,
                title=item.get("title", ""),
                body=body,
                summary=item.get("description", "")[:500],
                author=None,
                language="en",
                published_at=published_at,
                collected_at=datetime.now(UTC),
                collection_source="api:gnews",
            )
        )

    logger.info(
        "GNews: fetched %d articles (from %d total)", len(articles), len(data.get("articles", []))
    )
    return [a for a in articles if a.url and a.title]
