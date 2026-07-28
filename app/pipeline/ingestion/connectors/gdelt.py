from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.pipeline.ingestion.normalise import NormalisedArticle, detect_language, domain_from_url
from app.pipeline.ingestion.outlets import resolve_outlet

logger = logging.getLogger(__name__)

_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
_MAX_RECORDS = 250  # API maximum; was previously left at the 75 default
_TIMEOUT = 30.0

# The DOC 2.0 API indexes back to 2017 but only *serves* a rolling three-month window:
# STARTDATETIME/ENDDATETIME must fall inside it. Deeper history lives in GDELT's
# 15-minute GKG file archive, which is a separate ingestion path — see
# docs/data-model.md on historical backfill.
MAX_LOOKBACK_DAYS = 90

_DATE_FORMAT = "%Y%m%d%H%M%S"


def _window(start: datetime | None, end: datetime | None) -> dict[str, str]:
    """Clamp a requested window to what the API will actually serve."""
    if start is None and end is None:
        return {}
    now = datetime.now(UTC)
    floor = now - timedelta(days=MAX_LOOKBACK_DAYS)
    start = max(start or floor, floor)
    end = min(end or now, now)
    if start >= end:
        return {}
    return {
        "startdatetime": start.strftime(_DATE_FORMAT),
        "enddatetime": end.strftime(_DATE_FORMAT),
    }


async def fetch(
    db: AsyncSession,
    query: str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[NormalisedArticle]:
    """Fetch articles from the GDELT full-text search API.

    Unlike the other connectors, GDELT indexes hundreds of thousands of outlets rather
    than a curated handful — that breadth is the entire reason it is in the stack. The
    previous implementation resolved each article against a map of the 31 seeded
    outlets and discarded everything else, throwing that breadth away. Outlets are now
    created on discovery instead (app/pipeline/ingestion/outlets.py).

    ``query`` is required by the API and has no wildcard: a broad term or an operator
    such as a language or country filter is needed to sweep general coverage.

    GDELT supplies no article body, so records arrive title-only. That is fine for
    clustering and coverage distribution, and contributes nothing to framing analysis,
    which needs prose (docs/political-leaning-design.md).
    """
    params: dict[str, str | int] = {
        "query": query,
        "mode": "artlist",
        "maxrecords": _MAX_RECORDS,
        "format": "json",
        "sort": "datedesc",
        **_window(start, end),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.error("GDELT API error: %s", exc)
        return []

    items = data.get("articles", [])
    articles = []
    for item in items:
        url = item.get("url", "")
        title = item.get("title", "")
        if not url or not title:
            continue

        outlet_id = await resolve_outlet(domain_from_url(url), db)
        if outlet_id is None:
            continue

        try:
            # GDELT seendate format: YYYYMMDDTHHMMSSZ
            published_at = datetime.strptime(item.get("seendate", ""), "%Y%m%dT%H%M%SZ").replace(
                tzinfo=UTC
            )
        except ValueError:
            published_at = datetime.now(UTC)

        articles.append(
            NormalisedArticle(
                url=url,
                outlet_id=outlet_id,
                title=title,
                body="",  # GDELT does not provide body text
                summary="",
                author=None,
                # GDELT reports language as a name ("English"); detect from the title
                # instead so the column stays BCP 47 like every other connector.
                language=detect_language(title),
                published_at=published_at,
                collected_at=datetime.now(UTC),
                collection_source="api:gdelt",
            )
        )

    logger.info("GDELT: kept %d of %d articles returned", len(articles), len(items))
    return articles
