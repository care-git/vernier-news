from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.cache.clusters import get_cluster_summary
from app.database import get_db
from app.models.cluster import Cluster
from app.models.user import User
from app.schemas.cluster import ClusterSummary

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("/", response_model=list[ClusterSummary])
async def list_clusters(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    result = await db.execute(
        select(Cluster.id).where(Cluster.active.is_(True)).limit(50)
    )
    ids = result.scalars().all()
    summaries = []
    for cid in ids:
        summary = await get_cluster_summary(cid)
        if summary:
            summaries.append(summary)
    return summaries


@router.get("/{cluster_id}", response_model=ClusterSummary)
async def get_cluster(
    cluster_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    summary = await get_cluster_summary(cluster_id)
    if summary:
        return summary

    # Cache miss — return minimal data from DB.
    result = await db.execute(select(Cluster).where(Cluster.id == cluster_id))
    cluster = result.scalar_one_or_none()
    if cluster is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
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
