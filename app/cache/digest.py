from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.clusters import get_cluster_summary
from app.models.category import Category
from app.models.cluster import Cluster
from app.models.user import User, UserPreferences
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

_TTL = 3600  # 1 hour
_KEY = "digest:{}"
_CLUSTERS_PER_CATEGORY = 10


async def _clusters_for_category(category_slug: str, db: AsyncSession) -> list[dict]:
    """Return up to N cached cluster summaries for a given category slug."""
    result = await db.execute(
        select(Cluster.id)
        .join(Category, Category.id == Cluster.category_id)
        .where(Cluster.active == True)  # noqa: E712
        .where(Category.slug == category_slug)
        .order_by(Cluster.total_source_count.desc(), Cluster.last_updated_at.desc())
        .limit(_CLUSTERS_PER_CATEGORY)
    )
    cluster_ids = result.scalars().all()

    summaries = []
    for cid in cluster_ids:
        summary = await get_cluster_summary(cid)
        if summary:
            summaries.append(summary)

    return summaries


async def precompute_all_digests(db: AsyncSession) -> int:
    """Build and cache digest payloads for every user that has preferences set.

    Returns the number of digests written to Redis.
    """
    users_result = await db.execute(
        select(User.id, UserPreferences.categories)
        .join(UserPreferences, UserPreferences.user_id == User.id)
    )
    users = users_result.all()

    # All available category slugs for fallback (users with no category preferences).
    all_slugs_result = await db.execute(select(Category.slug))
    all_slugs = all_slugs_result.scalars().all()

    count = 0
    for user_id, categories_pref in users:
        # categories is stored as a JSON list of slugs, e.g. ["politics", "technology"]
        if categories_pref and isinstance(categories_pref, list):
            slugs = [s for s in categories_pref if isinstance(s, str)]
        else:
            slugs = list(all_slugs)

        digest: dict = {
            "user_id": user_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "categories": {},
        }

        for slug in slugs:
            summaries = await _clusters_for_category(slug, db)
            if summaries:
                digest["categories"][slug] = summaries

        await redis_client.set(_KEY.format(user_id), json.dumps(digest), ex=_TTL)
        count += 1

    logger.info("precomputed %d user digests", count)
    return count


async def get_digest(user_id: int) -> dict | None:
    """Return the cached digest for a user, or None if not yet computed."""
    raw = await redis_client.get(_KEY.format(user_id))
    return json.loads(raw) if raw else None
