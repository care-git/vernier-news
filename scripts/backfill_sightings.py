"""Populate `article_sightings` from the corpus collected before sightings existed.

    make backfill-sightings
    # docker compose exec api python -m scripts.backfill_sightings

Two passes:

    1. Every article that is not itself a duplicate gets a sighting for its own URL,
       so "all URL forms for this article" is a single query rather than a union of
       the articles table and this one.
    2. Every article marked 'duplicate' has its URL and collection path recorded
       against the article it duplicates — the keeper being the earliest article
       sharing that outlet, headline and URL path.

The duplicate rows themselves are left in place and stay marked. Per the
mark-never-delete policy in docs/data-model.md they are evidence, not waste, and they
are already excluded from clustering.

Idempotent: both passes are ON CONFLICT DO NOTHING against the (article_id, url)
unique constraint, so re-running adds only what is missing.

To revert:
    truncate article_sightings;
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

from app.database import SessionLocal
from app.pipeline.dedup import CONTENT_TYPE_DUPLICATE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("backfill_sightings")

# Mirrors canonical_path() in app/pipeline/ingestion/normalise.py: strip fragment,
# then query, then scheme and host, then any trailing slash.
_PATH = (
    r"lower(rtrim(regexp_replace("
    r"split_part(split_part(url, '#', 1), '?', 1), '^https?://[^/]+', ''), '/'))"
)
# Feeds vary internal spacing in a headline; group on the collapsed form.
_TITLE = r"regexp_replace(btrim(title), '\s+', ' ', 'g')"

_OWN_URLS = """
    insert into article_sightings (article_id, url, collection_source, first_seen_at)
    select id, url, collection_source, collected_at
    from articles
    where content_type is distinct from :duplicate
    on conflict do nothing
"""

# first_value over the same partition the duplicate classification used, so each
# duplicate resolves to exactly the article mark_repeats considered its original.
_DUPLICATE_URLS = f"""
    with norm as (
        select id, url, collection_source, collected_at, content_type,
               first_value(id) over (
                   partition by outlet_id, {_TITLE}, {_PATH}
                   order by published_at asc nulls last, id asc
               ) as keeper_id
        from articles
    )
    insert into article_sightings (article_id, url, collection_source, first_seen_at)
    select keeper_id, url, collection_source, collected_at
    from norm
    where content_type = :duplicate and keeper_id <> id
    on conflict do nothing
"""

_SUMMARY = """
    select count(*) as sightings,
           count(distinct article_id) as articles,
           count(*) - count(distinct article_id) as extra_forms
    from article_sightings
"""


async def _run(db) -> None:
    params = {"duplicate": CONTENT_TYPE_DUPLICATE}

    own = await db.execute(text(_OWN_URLS), params)
    logger.info("recorded %d articles under their own URL", own.rowcount)

    dupes = await db.execute(text(_DUPLICATE_URLS), params)
    logger.info("attached %d duplicate URL forms to the article they duplicate", dupes.rowcount)

    await db.commit()

    row = (await db.execute(text(_SUMMARY))).one()
    logger.info(
        "article_sightings now holds %d rows across %d articles (%d extra URL forms)",
        row.sightings,
        row.articles,
        row.extra_forms,
    )


async def main() -> None:
    async with SessionLocal() as db:
        await _run(db)


if __name__ == "__main__":
    asyncio.run(main())
