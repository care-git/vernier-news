from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.category import Category
from app.models.cluster import ArticleCluster, Cluster
from app.models.outlet import Outlet
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

_TTL = 3600  # 1 hour
_KEY = "cluster_summary:{}"


async def _build_summary(cluster: Cluster, category_slug: str | None, db: AsyncSession) -> dict:
    # Headline from the earliest article in the cluster.
    headline_row = await db.execute(
        select(Article.title)
        .join(ArticleCluster, ArticleCluster.article_id == Article.id)
        .where(ArticleCluster.cluster_id == cluster.id)
        .order_by(ArticleCluster.joined_at.asc())
        .limit(1)
    )
    headline = headline_row.scalar_one_or_none() or ""

    # Political spread and country list from cluster member outlets.
    outlet_rows = await db.execute(
        select(Outlet.country, Outlet.political_leaning_lr)
        .join(Article, Article.outlet_id == Outlet.id)
        .join(ArticleCluster, ArticleCluster.article_id == Article.id)
        .where(ArticleCluster.cluster_id == cluster.id)
    )
    rows = outlet_rows.all()
    countries = list({r.country for r in rows if r.country})
    leanings = [r.political_leaning_lr for r in rows if r.political_leaning_lr is not None]

    political_spread = None
    if leanings:
        political_spread = {
            "mean": round(sum(leanings) / len(leanings), 3),
            "min": round(min(leanings), 3),
            "max": round(max(leanings), 3),
        }

    return {
        "id": cluster.id,
        "headline": headline,
        "total_source_count": cluster.total_source_count,
        "independent_source_count": cluster.independent_source_count,
        "category": category_slug,
        "first_published_at": (
            cluster.first_published_at.isoformat() if cluster.first_published_at else None
        ),
        "last_updated_at": cluster.last_updated_at.isoformat(),
        "political_spread": political_spread,
        "countries": countries,
    }


async def precompute_cluster_summaries(db: AsyncSession) -> int:
    """Build and cache summary cards for all active clusters.

    Returns the number of summaries written to Redis.
    """
    result = await db.execute(
        select(Cluster, Category.slug.label("category_slug"))
        .outerjoin(Category, Category.id == Cluster.category_id)
        .where(Cluster.active == True)  # noqa: E712
    )
    rows = result.all()

    count = 0
    for row in rows:
        cluster: Cluster = row[0]
        category_slug: str | None = row.category_slug
        try:
            summary = await _build_summary(cluster, category_slug, db)
            await redis_client.set(_KEY.format(cluster.id), json.dumps(summary), ex=_TTL)
            count += 1
        except Exception:
            logger.exception("failed to build summary for cluster %d", cluster.id)

    logger.info("precomputed %d cluster summaries", count)
    return count


async def get_cluster_summary(cluster_id: int) -> dict | None:
    """Return the cached summary for a cluster, or None if not yet computed."""
    raw = await redis_client.get(_KEY.format(cluster_id))
    return json.loads(raw) if raw else None


async def invalidate_cluster(cluster_id: int) -> None:
    """Remove a cluster's cached summary so it is recomputed on next pass."""
    await redis_client.delete(_KEY.format(cluster_id))
