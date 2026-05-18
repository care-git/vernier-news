from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.pipeline.ingestion.normalise import NormalisedArticle


async def generate_embedding(text: str) -> list[float]:
    """Generate a 384-dimension embedding using all-MiniLM-L6-v2."""
    ...


async def get_wire_tier(
    article: NormalisedArticle,
    embedding: list[float],
    db: AsyncSession,
) -> tuple[int, float]:
    """Return (wire_tier, similarity_score) for the article against recent corpus.

    Tiers:
        0 — known wire service outlet
        1 — cosine similarity >0.88 within 6h (high-confidence wire copy)
        2 — similarity 0.70–0.88 within 3h or matching byline (probable wire)
        3 — similarity 0.62–0.70 within 4h (suspected, review queue)
        4 — no match (original / independent)
    """
    ...


async def is_duplicate(embedding: list[float], db: AsyncSession) -> bool:
    """Return True if an identical article (similarity >0.99) already exists."""
    ...
