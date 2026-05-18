from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.pipeline.ingestion.normalise import NormalisedArticle


def extract_entities(text: str) -> list[str]:
    """Run spaCy NER and return a deduplicated list of entity strings."""
    ...


async def assign_cluster(
    article_id: int,
    embedding: list[float],
    entities: list[str],
    published_at,
    db: AsyncSession,
) -> int:
    """Assign the article to an existing cluster or create a new one.

    Returns the cluster_id.
    """
    ...


async def update_cluster_metadata(cluster_id: int, db: AsyncSession) -> None:
    """Recompute source counts, geographic spread, and status for a cluster."""
    ...
