from __future__ import annotations

from typing import AsyncIterator

from app.pipeline.ingestion.normalise import NormalisedArticle


async def ingest_opml(opml_path: str) -> AsyncIterator[NormalisedArticle]:
    """Parse an OPML file and yield normalised articles from all listed feeds."""
    ...


async def ingest_feed(feed_url: str, outlet_id: int) -> list[NormalisedArticle]:
    """Fetch and parse a single RSS/Atom feed, returning normalised articles."""
    ...
