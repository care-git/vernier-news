"""Resolve an article's domain to an outlet, creating the outlet if it is new.

Ingestion used to hold an ``outlet_map`` of seeded domains and silently drop every
article from anywhere else. That inverted the intended relationship: the corpus should
discover its sources from the articles it collects, rather than being capped by a
hand-curated list of 31. See docs/data-model.md.

Discovered outlets carry ``discovered_at`` and no political leaning. Leaning is
computed rather than hand-assigned (docs/political-leaning-design.md) — which is not
optional at this scale, since per-outlet MBFC scores cannot be maintained by hand for
tens of thousands of sources.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outlet import Outlet

logger = logging.getLogger(__name__)


async def resolve_outlet(domain: str, db: AsyncSession, *, name: str | None = None) -> int | None:
    """Return the outlet id for ``domain``, creating a record the first time it is seen.

    Returns None only when the domain is empty — an article with no resolvable source
    has no provenance and cannot be cited, which the platform requires of every record.

    ``name`` defaults to the domain: GDELT and the other aggregator APIs supply no
    display name, and inventing one from the domain is more honest than guessing.
    Enrichment is a later pass.
    """
    if not domain:
        return None

    existing = await db.scalar(select(Outlet.id).where(Outlet.domain == domain))
    if existing is not None:
        return existing

    # ON CONFLICT rather than a plain insert: several connectors run inside one task
    # and can meet the same new domain in the same pass. Column defaults are declared
    # Python-side on the model, so a Core insert has to supply them explicitly.
    await db.execute(
        pg_insert(Outlet)
        .values(
            domain=domain,
            name=name or domain,
            discovered_at=datetime.now(UTC),
            wire_service=False,
            active=True,
        )
        .on_conflict_do_nothing(index_elements=["domain"])
    )
    outlet_id = await db.scalar(select(Outlet.id).where(Outlet.domain == domain))
    if outlet_id is not None:
        logger.info("discovered outlet %s (id=%d)", domain, outlet_id)
    return outlet_id
