from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx

from app.pipeline.ingestion.normalise import NormalisedArticle

logger = logging.getLogger(__name__)

_BASE = "https://api.nytimes.com/svc/topstories/v2/{section}.json"
_SECTIONS = ["home", "world", "us", "politics", "technology", "science", "health"]
_TIMEOUT = 20.0


async def fetch(outlet_id: int, api_key: str) -> list[NormalisedArticle]:
    """Fetch top stories from the NYT Top Stories API across key sections."""
    articles: list[NormalisedArticle] = []
    seen_urls: set[str] = set()

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        for section in _SECTIONS:
            try:
                resp = await client.get(
                    _BASE.format(section=section),
                    params={"api-key": api_key},
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                logger.error("NYT API error (section=%s): %s", section, exc)
                continue

            for item in data.get("results", []):
                url = item.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                try:
                    published_at = datetime.fromisoformat(
                        item.get("published_date", "").replace("Z", "+00:00")
                    )
                except ValueError:
                    published_at = datetime.now(UTC)

                byline = item.get("byline", "").removeprefix("By ") or None
                abstract = item.get("abstract", "")

                articles.append(
                    NormalisedArticle(
                        url=url,
                        outlet_id=outlet_id,
                        title=item.get("title", ""),
                        body=abstract,
                        summary=abstract[:500],
                        author=byline,
                        language="en",
                        published_at=published_at,
                        collected_at=datetime.now(UTC),
                        collection_source=f"api:nyt:{section}",
                    )
                )

    logger.info("NYT: fetched %d articles across %d sections", len(articles), len(_SECTIONS))
    return [a for a in articles if a.url and a.title]
