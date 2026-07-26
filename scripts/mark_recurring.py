"""Backfill `articles.content_type = 'recurring'` across the existing corpus.

    make mark-recurring
    # docker compose exec api python -m scripts.mark_recurring

The live pipeline flags recurring formats at ingest (app/pipeline/dedup.py), but
everything collected before that landed is unflagged. This marks the backlog using
the same rule: within each (outlet, exact title) group, the earliest article keeps
its story status and every later repeat is marked.

Marked articles are kept — several are future assets, notably the Guardian's daily
corrections column, which feeds the correction-record dimension of the feature
analysis system. They are only excluded from story clustering.

Idempotent: already-marked rows are left alone, so it is safe to re-run. It does not
touch existing cluster memberships — those clear on the next `make recluster`, which
skips marked articles.

To revert:
    update articles set content_type = null where content_type = 'recurring';
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

from app.database import SessionLocal
from app.pipeline.dedup import CONTENT_TYPE_RECURRING

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("mark_recurring")

# Rank within each (outlet, title) group; rank 1 is the original, the rest are repeats.
_RANKED = """
    select id, row_number() over (
        partition by outlet_id, title
        order by published_at asc nulls last, id asc
    ) as rn
    from articles
"""

_PREVIEW = f"""
    with ranked as ({_RANKED})
    select o.name, left(a.title, 52) as title, count(*) as repeats
    from articles a
    join outlets o on o.id = a.outlet_id
    join ranked r on r.id = a.id
    where r.rn > 1 and a.content_type is null
    group by o.name, a.title
    order by repeats desc
"""

_UPDATE = f"""
    with ranked as ({_RANKED})
    update articles a set content_type = :content_type
    from ranked r
    where a.id = r.id and r.rn > 1 and a.content_type is null
"""

_CLUSTERED = """
    select count(*) from articles a
    join article_cluster ac on ac.article_id = a.id
    where a.content_type = :content_type
"""


async def _run(db) -> None:
    rows = (await db.execute(text(_PREVIEW))).all()
    if not rows:
        logger.info("no unmarked recurring articles found — nothing to do")
        return

    total = sum(r.repeats for r in rows)
    logger.info("%d repeats across %d (outlet, title) groups:", total, len(rows))
    print(f"\n{'outlet':<22}{'title':<54}{'repeats':>8}")
    for r in rows:
        print(f"{r.name[:21]:<22}{r.title:<54}{r.repeats:>8,}")

    result = await db.execute(text(_UPDATE), {"content_type": CONTENT_TYPE_RECURRING})
    await db.commit()
    logger.info("marked %d articles as '%s'", result.rowcount, CONTENT_TYPE_RECURRING)

    stale = await db.scalar(text(_CLUSTERED), {"content_type": CONTENT_TYPE_RECURRING})
    if stale:
        logger.info(
            "%d marked articles still hold cluster memberships — run `make recluster` "
            "to rebuild without them",
            stale,
        )


async def main() -> None:
    async with SessionLocal() as db:
        await _run(db)


if __name__ == "__main__":
    asyncio.run(main())
