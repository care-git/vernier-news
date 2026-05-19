from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx

from app.pipeline.ingestion.normalise import NormalisedArticle

logger = logging.getLogger(__name__)

_TOP_STORIES = "https://hacker-news.firebaseio.com/v1/topstories.json"
_ITEM = "https://hacker-news.firebaseio.com/v1/item/{}.json"
_FETCH_COUNT = 30  # top N stories per run
_CONCURRENCY = 5  # simultaneous item requests
_TIMEOUT = 15.0


async def _fetch_item(client: httpx.AsyncClient, item_id: int) -> dict | None:
    try:
        resp = await client.get(_ITEM.format(item_id))
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


async def fetch(outlet_map: dict[str, int]) -> list[NormalisedArticle]:
    """Fetch top Hacker News stories and attribute each to its linked outlet.

    Stories without an external URL (Ask HN, Show HN, etc.) are skipped.
    Stories whose domain is not in outlet_map are attributed to the HN outlet
    (news.ycombinator.com) using the HN item URL as the canonical URL.
    """
    hn_outlet_id = outlet_map.get("news.ycombinator.com")

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.get(_TOP_STORIES)
            resp.raise_for_status()
            top_ids: list[int] = resp.json()[:_FETCH_COUNT]
        except Exception as exc:
            logger.error("HN top stories fetch failed: %s", exc)
            return []

        # Fetch items with bounded concurrency.
        semaphore = asyncio.Semaphore(_CONCURRENCY)

        async def _bounded_fetch(item_id: int) -> dict | None:
            async with semaphore:
                return await _fetch_item(client, item_id)

        items = await asyncio.gather(*[_bounded_fetch(i) for i in top_ids])

    articles = []
    for item in items:
        if not item or item.get("type") != "story":
            continue

        title = item.get("title", "").strip()
        external_url = item.get("url", "")
        hn_url = f"https://news.ycombinator.com/item?id={item['id']}"
        published_at = datetime.fromtimestamp(item.get("time", 0), tz=UTC)

        if external_url:
            domain = urlparse(external_url).netloc.removeprefix("www.")
            outlet_id = outlet_map.get(domain)
            url = external_url
        else:
            outlet_id = None
            url = hn_url

        # Fall back to HN outlet for unrecognised domains or self-posts.
        if outlet_id is None:
            if hn_outlet_id is None:
                continue
            outlet_id = hn_outlet_id
            url = hn_url

        if not title:
            continue

        articles.append(
            NormalisedArticle(
                url=url,
                outlet_id=outlet_id,
                title=title,
                body="",  # HN does not provide article body
                summary="",
                author=item.get("by") or None,
                language="en",
                published_at=published_at,
                collected_at=datetime.now(UTC),
                collection_source="api:hackernews",
            )
        )

    logger.info("HN: fetched %d stories", len(articles))
    return articles
