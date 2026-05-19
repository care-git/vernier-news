from __future__ import annotations

import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from app.pipeline.ingestion.normalise import NormalisedArticle

logger = logging.getLogger(__name__)

_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
_MAX_RECORDS = 75
_TIMEOUT = 30.0


async def fetch(outlet_map: dict[str, int]) -> list[NormalisedArticle]:
    """Fetch recent articles from the GDELT full-text search API.

    Uses a broad query to capture top current news across all monitored sources.
    Articles are attributed to their outlet only when the source domain exists
    in outlet_map — others are skipped.
    """
    params = {
        "query": "*",
        "mode": "artlist",
        "maxrecords": _MAX_RECORDS,
        "format": "json",
        "sort": "datedesc",
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.error("GDELT API error: %s", exc)
        return []

    articles = []
    for item in data.get("articles", []):
        url = item.get("url", "")
        domain = urlparse(url).netloc.removeprefix("www.")
        outlet_id = outlet_map.get(domain)
        if outlet_id is None:
            continue

        raw_date = item.get("seendate", "")
        try:
            # GDELT seendate format: YYYYMMDDTHHMMSSZ
            published_at = datetime.strptime(raw_date, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            published_at = datetime.now(timezone.utc)

        title = item.get("title", "")
        articles.append(NormalisedArticle(
            url=url,
            outlet_id=outlet_id,
            title=title,
            body="",   # GDELT does not provide body text
            summary="",
            author=None,
            language=item.get("language", "unknown").lower()[:10],
            published_at=published_at,
            collected_at=datetime.now(timezone.utc),
            collection_source="api:gdelt",
        ))

    logger.info(
        "GDELT: fetched %d articles (from %d total)", len(articles), len(data.get("articles", []))
    )
    return [a for a in articles if a.url and a.title]
