"""Classify repeated headlines in the existing corpus into `articles.content_type`.

    make mark-repeats
    # docker compose exec api python -m scripts.mark_repeats

The live pipeline classifies at ingest (app/pipeline/dedup.py) and drops duplicate
URL forms before they are ever persisted. This applies the same rule to the backlog
collected before that landed, using the same discriminator:

    same outlet + same headline + same URL path  -> 'duplicate'
    same outlet + same headline + different path -> 'recurring'

The earliest article in each group always keeps its story status; only later repeats
are classified.

'duplicate' rows are the same page ingested twice under different URL forms — BBC RSS
links to bbc.com with campaign parameters while GNews returns the bare bbc.co.uk
link, and NYT publishes one story under two section paths. 'recurring' rows are real
articles on a genuinely new page that reuse a standing headline, and are kept: the
Guardian's daily corrections column feeds the correction-record dimension of the
feature analysis system.

Neither is story-clustered. Idempotent — it reclassifies from scratch on every run,
so it is safe to re-run after the rule changes. Titles are compared with internal
whitespace collapsed, matching what normalise() now stores, but existing rows are
not rewritten.

To revert:
    update articles set content_type = null
     where content_type in ('duplicate', 'recurring');
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

from app.database import SessionLocal
from app.pipeline.dedup import CONTENT_TYPE_DUPLICATE, CONTENT_TYPE_RECURRING

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("mark_repeats")

# Strip fragment, then query, then the scheme+host, then any trailing slash. Mirrors
# canonical_path() in app/pipeline/ingestion/normalise.py.
_PATH = (
    r"lower(rtrim(regexp_replace("
    r"split_part(split_part(url, '#', 1), '?', 1), '^https?://[^/]+', ''), '/'))"
)
# Feeds vary internal spacing in a headline; group on the collapsed form.
_TITLE = r"regexp_replace(btrim(title), '\s+', ' ', 'g')"

# title_rn > 1 means the outlet has run this headline before. path_rn > 1 additionally
# means an earlier article shares its URL path — the same page, so a duplicate rather
# than a new instalment. Both windows order identically, and the path partition is a
# subset of the title partition, so the two ranks stay consistent.
_NORMALISED = f"""
    select id,
           row_number() over (
               partition by outlet_id, {_TITLE}
               order by published_at asc nulls last, id asc
           ) as title_rn,
           row_number() over (
               partition by outlet_id, {_TITLE}, {_PATH}
               order by published_at asc nulls last, id asc
           ) as path_rn
    from articles
"""

_CLASSIFY = f"""
    with norm as ({_NORMALISED})
    select id, case when path_rn > 1 then :duplicate else :recurring end as content_type
    from norm
    where title_rn > 1
"""

_PREVIEW = f"""
    with classified as ({_CLASSIFY})
    select c.content_type, count(*) as articles,
           count(distinct (a.outlet_id, {_TITLE})) as headlines
    from classified c
    join articles a on a.id = c.id
    group by c.content_type
    order by articles desc
"""

_APPLY = f"""
    with classified as ({_CLASSIFY})
    update articles a set content_type = c.content_type
    from classified c
    where a.id = c.id
"""

# Only the values this script owns, so any future content_type is left untouched.
_RESET = "update articles set content_type = null where content_type = any(:owned)"

_STALE = """
    select count(*) from articles a
    join article_cluster ac on ac.article_id = a.id
    where a.content_type is not null
"""


async def _run(db) -> None:
    params = {"duplicate": CONTENT_TYPE_DUPLICATE, "recurring": CONTENT_TYPE_RECURRING}
    owned = [CONTENT_TYPE_DUPLICATE, CONTENT_TYPE_RECURRING]

    rows = (await db.execute(text(_PREVIEW), params)).all()
    if not rows:
        logger.info("no repeated headlines found — nothing to classify")
        return

    print(f"\n{'content_type':<16}{'articles':>10}{'distinct headlines':>22}")
    for r in rows:
        print(f"{r.content_type:<16}{r.articles:>10,}{r.headlines:>22,}")
    print()

    reset = await db.execute(text(_RESET), {"owned": owned})
    result = await db.execute(text(_APPLY), params)
    await db.commit()
    logger.info(
        "cleared %d previous marks, classified %d articles", reset.rowcount, result.rowcount
    )

    stale = await db.scalar(text(_STALE))
    if stale:
        logger.info(
            "%d classified articles still hold cluster memberships — run `make recluster` "
            "to rebuild without them",
            stale,
        )


async def main() -> None:
    async with SessionLocal() as db:
        await _run(db)


if __name__ == "__main__":
    asyncio.run(main())
