from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


async def precompute_cluster_summaries(db: AsyncSession) -> int:
    """Build and cache summary cards for all active clusters.

    Returns the number of summaries written to Redis.
    """
    ...


async def get_cluster_summary(cluster_id: int) -> dict | None:
    """Return the cached summary for a cluster, or None if not yet computed."""
    ...


async def invalidate_cluster(cluster_id: int) -> None:
    """Remove a cluster's cached summary so it is recomputed on next pass."""
    ...
