"""Fill in `registrable_domain` and `source_type` across the outlets table.

    make classify-outlets
    # docker compose exec api python -m scripts.classify_outlets

Ingestion classifies each outlet as it is discovered, but the 1,600-odd found before
these columns existed carry neither, and the seed lists in
app/pipeline/ingestion/sources.py will keep growing as new kinds of publisher turn up.

Outlets seeded by scripts/seed.py (discovered_at IS NULL) are the curated news library
and are marked 'news'. Journalism cannot be detected from a domain, so nothing else
is: discovered outlets get only what their domain shape gives away, and most stay
unclassified.

Idempotent, and safe to re-run after editing the seed lists: it recomputes rather than
filling gaps, so a domain moved between categories moves in the database too. Nothing
is ever excluded on the basis of source_type — the column labels, it does not filter
(docs/data-model.md).

To revert:
    update outlets set registrable_domain = null, source_type = null;
"""

from __future__ import annotations

import asyncio
import logging
from collections import Counter

from sqlalchemy import func, select, update

from app.database import SessionLocal
from app.models.outlet import Outlet
from app.pipeline.ingestion.sources import SOURCE_TYPE_NEWS, classify_source, registrable_domain

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("classify_outlets")

_SIBLINGS = (
    select(Outlet.registrable_domain, func.count(Outlet.id).label("outlets"))
    .where(Outlet.registrable_domain.isnot(None))
    .group_by(Outlet.registrable_domain)
    .having(func.count(Outlet.id) > 1)
    .order_by(func.count(Outlet.id).desc())
)


async def _run(db) -> None:
    rows = (await db.execute(select(Outlet.id, Outlet.domain, Outlet.discovered_at))).all()
    if not rows:
        logger.info("no outlets to classify")
        return

    counts: Counter[str] = Counter()
    payload = []
    for outlet_id, domain, discovered_at in rows:
        # A curated seed entry is a news outlet by construction; a discovered one is
        # only whatever its domain shape gives away.
        source_type = classify_source(domain)
        if source_type is None and discovered_at is None:
            source_type = SOURCE_TYPE_NEWS
        counts[source_type or "unclassified"] += 1
        payload.append(
            {
                "id": outlet_id,
                "registrable_domain": registrable_domain(domain),
                "source_type": source_type,
            }
        )

    # ORM bulk update by primary key: no explicit WHERE, because SQLAlchemy derives it
    # from the "id" in each dict. Adding one instead makes it a criteria-based update,
    # which cannot synchronise ORM state and raises.
    await db.execute(update(Outlet), payload)
    await db.commit()
    logger.info("classified %d outlets", len(payload))

    print(f"\n{'source_type':<18}{'outlets':>9}")
    for source_type, count in counts.most_common():
        print(f"{source_type:<18}{count:>9,}")

    siblings = (await db.execute(_SIBLINGS)).all()
    total = sum(r.outlets for r in siblings)
    print(f"\n{len(siblings):,} registrable domains group {total:,} outlets. Largest:")
    for row in siblings[:15]:
        print(f"  {row.registrable_domain:<38}{row.outlets:>4} outlets")


async def main() -> None:
    async with SessionLocal() as db:
        await _run(db)


if __name__ == "__main__":
    asyncio.run(main())
