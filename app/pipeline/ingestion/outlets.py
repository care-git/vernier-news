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

import pycountry
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outlet import Outlet

logger = logging.getLogger(__name__)


def country_code(value: str | None) -> str | None:
    """Map a country name or code to ISO 3166-1 alpha-2, or None if unrecognisable.

    Sources disagree on format: GDELT reports a country *name* ("United Kingdom")
    while ``Outlet.country`` is alpha-2, and other connectors may send a code already.
    ``pycountry.lookup`` accepts alpha-2, alpha-3, name, official name and common
    name, so both forms resolve without a hand-maintained table.

    Unrecognised values are logged rather than guessed at — a wrong country silently
    corrupts coverage-distribution analysis, which is per-region.
    """
    if not value:
        return None
    try:
        return pycountry.countries.lookup(value.strip()).alpha_2
    except LookupError:
        logger.info("unmapped country value from a connector: %r", value)
        return None


async def resolve_outlet(
    domain: str,
    db: AsyncSession,
    *,
    name: str | None = None,
    country: str | None = None,
) -> int | None:
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
            country=country_code(country),
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
