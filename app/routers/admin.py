from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy import func, select

from app.config import settings
from app.database import get_db
from app.models.article import Article
from app.models.cluster import Cluster
from app.models.outlet import Outlet
from app.redis_client import redis_client
from app.worker import celery_app

router = APIRouter(prefix="/admin", tags=["admin"])

_api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def _require_admin_key(key: str | None = Depends(_api_key_header)) -> None:
    if settings.admin_api_key and key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="invalid admin key")


@router.get("/health")
async def admin_health(
    _: None = Depends(_require_admin_key),
    db=Depends(get_db),
) -> dict[str, Any]:
    """DB row counts, Redis cache stats, and Celery queue depth."""
    article_count = await db.scalar(select(func.count()).select_from(Article))
    cluster_count = await db.scalar(select(func.count()).select_from(Cluster))
    outlet_count = await db.scalar(select(func.count()).select_from(Outlet).where(Outlet.active == True))  # noqa: E712
    uncategorised = await db.scalar(
        select(func.count()).select_from(Article).where(Article.category_id == None)  # noqa: E711
    )

    cluster_keys = await redis_client.keys("cluster_summary:*")
    digest_keys = await redis_client.keys("digest:*")
    celery_queue_depth = await redis_client.llen("celery")

    return {
        "database": {
            "articles": article_count,
            "clusters": cluster_count,
            "active_outlets": outlet_count,
            "uncategorised_articles": uncategorised,
        },
        "redis": {
            "cluster_summaries_cached": len(cluster_keys),
            "digests_cached": len(digest_keys),
            "celery_queue_depth": celery_queue_depth,
        },
    }


@router.post("/ingest")
async def admin_ingest(_: None = Depends(_require_admin_key)) -> dict[str, str]:
    """Queue an immediate ingest_feeds run."""
    result = celery_app.send_task("pipeline.ingest_feeds")
    return {"task_id": result.id, "status": "queued"}


@router.get("/clusters/stats")
async def admin_cluster_stats(
    _: None = Depends(_require_admin_key),
    db=Depends(get_db),
) -> dict[str, Any]:
    """Cluster activity over the last 24 hours."""
    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)
    cutoff_48h = now - timedelta(hours=48)

    created = await db.scalar(
        select(func.count()).select_from(Cluster).where(Cluster.first_published_at >= cutoff_24h)
    )
    updated = await db.scalar(
        select(func.count()).select_from(Cluster).where(
            Cluster.last_updated_at >= cutoff_24h,
            Cluster.first_published_at < cutoff_24h,
        )
    )
    dormant = await db.scalar(
        select(func.count()).select_from(Cluster).where(
            Cluster.active == True,  # noqa: E712
            Cluster.last_updated_at < cutoff_48h,
        )
    )

    return {
        "period_hours": 24,
        "created": created,
        "updated": updated,
        "dormant": dormant,
    }


@router.get("/sources")
async def admin_sources(
    _: None = Depends(_require_admin_key),
    db=Depends(get_db),
) -> dict[str, Any]:
    """Active and inactive outlet summary."""
    result = await db.execute(select(Outlet.domain, Outlet.active, Outlet.wire_service))
    rows = result.all()

    inactive = [r.domain for r in rows if not r.active]
    wire_services = [r.domain for r in rows if r.wire_service]

    return {
        "total": len(rows),
        "active": sum(1 for r in rows if r.active),
        "inactive": len(inactive),
        "wire_services": len(wire_services),
        "inactive_domains": inactive,
    }
