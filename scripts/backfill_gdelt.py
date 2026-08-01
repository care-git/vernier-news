"""Walk GDELT backwards through its served window, storing articles without embedding.

    make backfill-gdelt
    # docker compose exec api python -m scripts.backfill_gdelt

The live task (pipeline.sweep_gdelt) walks *forward* from the newest GDELT article we
hold and idles once it catches up. This walks *backwards* from the oldest one, filling
in history until it reaches the limit of what the DOC API will serve — three months.

Articles are stored **without embeddings**, which is what makes the scale affordable:
an embedding plus its index entry costs roughly 10 KB per article against 400 bytes
for the record alone, so ninety days of sweeping is the difference between ~65 GB and
~3 GB. The vector is the one part that can be recreated at any time from stored text —
run `make reembed` over whichever slice is worth embedding. Until then these articles
are deliberately absent from clustering, which filters on `embedding IS NOT NULL`.

Resumable and interruptible: the cursor is the corpus itself (the oldest GDELT article
held), and each window commits before the next request, so stopping it loses at most
one window. Re-run to continue.

Long-running by nature — GDELT permits one request every five seconds, so a full
ninety-day sweep is well over a day of wall time. Run it under screen or nohup, and
stop it whenever the corpus is large enough.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.config import settings
from app.database import SessionLocal
from app.models.article import Article
from app.pipeline import tuning
from app.pipeline.dedup import persist_article
from app.pipeline.ingestion.connectors import gdelt

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("backfill_gdelt")

# Windows to sweep before exiting, so a run is bounded and re-running continues. At one
# request per five seconds this is a little under three hours.
_WINDOWS_PER_RUN = 2000


async def _oldest_gdelt_article(db) -> datetime | None:
    return await db.scalar(
        select(func.min(Article.published_at)).where(Article.collection_source == "api:gdelt")
    )


async def _run(db) -> None:
    await tuning.refresh(db)

    floor = datetime.now(UTC) - timedelta(days=gdelt.MAX_LOOKBACK_DAYS)
    cursor = await _oldest_gdelt_article(db) or datetime.now(UTC)
    if cursor.tzinfo is None:
        cursor = cursor.replace(tzinfo=UTC)

    if cursor <= floor:
        logger.info("already back at the API's %d-day limit", gdelt.MAX_LOOKBACK_DAYS)
        return

    logger.info(
        "sweeping backwards from %s to %s (%d windows of %d min max this run)",
        cursor,
        floor,
        _WINDOWS_PER_RUN,
        gdelt.SWEEP_WINDOW_MINUTES,
    )

    window = timedelta(minutes=gdelt.SWEEP_WINDOW_MINUTES)
    saved = 0
    for swept in range(_WINDOWS_PER_RUN):
        if cursor <= floor:
            logger.info("reached the API's %d-day limit", gdelt.MAX_LOOKBACK_DAYS)
            break

        start = max(cursor - window, floor)
        if swept:
            await asyncio.sleep(gdelt.RATE_LIMIT_SECONDS)
        articles = await gdelt.fetch(db, settings.gdelt_query, start=start, end=cursor)

        for article in articles:
            try:
                # embed=False is the whole point: capture now, embed selectively later.
                if await persist_article(article, db, embed=False) is not None:
                    saved += 1
            except Exception:
                logger.exception("failed to persist GDELT article: %s", article.url)

        # Commit per window so an interrupted run keeps everything before it.
        await db.commit()
        cursor = start

        if swept % 20 == 0:
            logger.info("cursor %s — %d articles saved so far", cursor, saved)

    logger.info(
        "done: %d articles saved, cursor at %s. Re-run to continue; `make reembed` to "
        "embed what is worth clustering.",
        saved,
        cursor,
    )


async def main() -> None:
    async with SessionLocal() as db:
        await _run(db)


if __name__ == "__main__":
    asyncio.run(main())
