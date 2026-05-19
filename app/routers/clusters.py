from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.cluster import Cluster
from app.models.user import User

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("/")
async def list_clusters(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    result = await db.execute(select(Cluster).where(Cluster.active.is_(True)).limit(50))
    return [
        {
            "id": c.id,
            "total_source_count": c.total_source_count,
            "independent_source_count": c.independent_source_count,
        }
        for c in result.scalars()
    ]


@router.get("/{cluster_id}")
async def get_cluster(
    cluster_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    result = await db.execute(select(Cluster).where(Cluster.id == cluster_id))
    cluster = result.scalar_one_or_none()
    if cluster is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
    return {
        "id": cluster.id,
        "total_source_count": cluster.total_source_count,
        "independent_source_count": cluster.independent_source_count,
        "active": cluster.active,
    }
