from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.cache.clusters import get_cluster_summary
from app.database import get_db
from app.models.article import Article
from app.models.cluster import ArticleCluster, Cluster
from app.models.outlet import Outlet
from app.models.user import User
from app.schemas.cluster import ClusterDetail, ClusterSummary

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("/", response_model=list[ClusterSummary])
async def list_clusters(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    result = await db.execute(select(Cluster.id).where(Cluster.active.is_(True)).limit(50))
    ids = result.scalars().all()
    summaries = []
    for cid in ids:
        summary = await get_cluster_summary(cid)
        if summary:
            summaries.append(summary)
    return summaries


async def _load_sources(cluster_id: int, db: AsyncSession) -> list[dict]:
    """Fetch every member article of a cluster with its outlet context.

    Ordered by publication time (earliest first); Postgres sorts NULL timestamps
    last for ascending order.
    """
    result = await db.execute(
        select(Article, Outlet, ArticleCluster.independence_score)
        .join(ArticleCluster, ArticleCluster.article_id == Article.id)
        .join(Outlet, Outlet.id == Article.outlet_id)
        .where(ArticleCluster.cluster_id == cluster_id)
        .order_by(Article.published_at.asc())
    )
    sources = []
    for article, outlet, independence_score in result.all():
        sources.append(
            {
                "article_id": article.id,
                "title": article.title,
                "url": article.url,
                "published_at": (
                    article.published_at.isoformat() if article.published_at else None
                ),
                "author": article.author,
                "wire_tier": article.wire_tier,
                "independence_score": independence_score,
                "outlet": {
                    "id": outlet.id,
                    "name": outlet.name,
                    "domain": outlet.domain,
                    "country": outlet.country,
                    "political_leaning_lr": outlet.political_leaning_lr,
                    "parent_org_name": outlet.parent_org_name,
                },
            }
        )
    return sources


def _minimal_summary(cluster: Cluster) -> dict:
    """Summary-level fields from the cluster row alone (used on cache miss)."""
    return {
        "id": cluster.id,
        "headline": "",
        "total_source_count": cluster.total_source_count,
        "independent_source_count": cluster.independent_source_count,
        "category": None,
        "first_published_at": (
            cluster.first_published_at.isoformat() if cluster.first_published_at else None
        ),
        "last_updated_at": cluster.last_updated_at.isoformat(),
        "political_spread": None,
        "countries": [],
    }


@router.get("/{cluster_id}", response_model=ClusterDetail)
async def get_cluster(
    cluster_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    result = await db.execute(select(Cluster).where(Cluster.id == cluster_id))
    cluster = result.scalar_one_or_none()
    if cluster is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")

    # Summary-level fields come from the precomputed cache; fall back to the row.
    summary = await get_cluster_summary(cluster_id) or _minimal_summary(cluster)

    # The full member list is on-demand (analytical layer), always from the DB.
    sources = await _load_sources(cluster_id, db)
    counts = Counter(s["outlet"]["country"] for s in sources if s["outlet"]["country"] is not None)
    country_counts = [{"country": c, "count": n} for c, n in counts.most_common()]

    return {**summary, "sources": sources, "country_counts": country_counts}
