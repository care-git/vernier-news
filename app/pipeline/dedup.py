from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.outlet import Outlet
from app.pipeline import tuning
from app.pipeline.ingestion.normalise import NormalisedArticle

logger = logging.getLogger(__name__)

# Loaded once per worker process on first call.
_model: SentenceTransformer | None = None

# Wire tier + dedup thresholds now live in the `settings` table — see
# app/pipeline/tuning.py.


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def generate_embedding(text: str) -> list[float]:
    """Generate a 384-dimension embedding using all-MiniLM-L6-v2."""
    return _get_model().encode(text, normalize_embeddings=True).tolist()


async def is_duplicate(url: str, embedding: list[float], db: AsyncSession) -> bool:
    """Return True if this article already exists (by URL or near-identical content).

    Near-identical: cosine similarity > 0.99 against any article in the last 72 hours.
    """
    url_check = await db.execute(select(Article.id).where(Article.url == url).limit(1))
    if url_check.scalar_one_or_none() is not None:
        return True

    t = tuning.current()
    cutoff = datetime.now(UTC) - timedelta(hours=t.dedup_window_hours)
    sim_check = await db.execute(
        select(Article.id)
        .where(Article.published_at >= cutoff)
        .where(Article.embedding.cosine_distance(embedding) < t.dedup_max_distance)
        .limit(1)
    )
    return sim_check.scalar_one_or_none() is not None


async def get_wire_tier(
    article: NormalisedArticle,
    embedding: list[float],
    db: AsyncSession,
) -> tuple[int, float]:
    """Compute the wire propagation tier for an article against the recent corpus.

    Phase 1: detection and logging only — no collapsing. Calibration in Phase 3.

    Returns (tier, best_similarity_score):
        0 — known wire service outlet
        1 — cosine similarity > 0.88 within 6h (high-confidence wire copy)
        2 — similarity 0.70–0.88 within 3h OR matching author byline (probable wire)
        3 — similarity 0.62–0.70 within 4h (suspected, review queue)
        4 — original / no match
    """
    outlet_result = await db.execute(
        select(Outlet.wire_service).where(Outlet.id == article.outlet_id)
    )
    if outlet_result.scalar_one_or_none():
        logger.debug("wire tier 0 (wire service outlet): %s", article.url)
        return 0, 1.0

    now = article.published_at or datetime.now(UTC)
    t = tuning.current()

    async def _best_match(window_hours: float) -> tuple[int | None, float]:
        cutoff = now - timedelta(hours=window_hours)
        result = await db.execute(
            select(
                Article.id,
                Article.embedding.cosine_distance(embedding).label("dist"),
                Article.author,
            )
            .where(Article.published_at >= cutoff)
            .where(Article.embedding.isnot(None))
            .order_by(Article.embedding.cosine_distance(embedding))
            .limit(1)
        )
        row = result.first()
        if row is None:
            return None, 0.0
        return row.id, 1.0 - row.dist

    _, sim_6h = await _best_match(t.tier1_window_hours)
    if sim_6h >= t.tier1_similarity:
        logger.info("wire tier 1 (sim=%.3f): %s", sim_6h, article.url)
        return 1, sim_6h

    match_id_3h, sim_3h = await _best_match(t.tier2_window_hours)
    if match_id_3h is not None and sim_3h >= t.tier2_similarity_low:
        # Author byline match is an additional Tier 2 signal; check below threshold too
        match_row = await db.execute(select(Article.author).where(Article.id == match_id_3h))
        match_author = match_row.scalar_one_or_none()
        author_match = (
            article.author and match_author and article.author.lower() == match_author.lower()
        )
        if sim_3h < t.tier2_similarity_high or author_match:
            logger.info(
                "wire tier 2 (sim=%.3f, author_match=%s): %s",
                sim_3h,
                author_match,
                article.url,
            )
            return 2, sim_3h

    _, sim_4h = await _best_match(t.tier3_window_hours)
    if t.tier3_similarity_low <= sim_4h < t.tier3_similarity_high:
        logger.info("wire tier 3 (sim=%.3f): %s", sim_4h, article.url)
        return 3, sim_4h

    return 4, max(sim_6h, sim_3h, sim_4h)


async def persist_article(article: NormalisedArticle, db: AsyncSession) -> Article | None:
    """Run the full dedup pipeline and persist the article if it is not a duplicate.

    Flow:
        1. Generate embedding from title + body excerpt
        2. Check for exact URL duplicate or near-identical content (returns None if found)
        3. Compute and log wire tier (Phase 1: log only, no collapsing)
        4. Write Article record to the database

    Returns the saved Article ORM object, or None if the article was a duplicate.
    """
    text = f"{article.title} {article.body[:500]}"
    embedding = generate_embedding(text)

    if await is_duplicate(article.url, embedding, db):
        logger.debug("duplicate skipped: %s", article.url)
        return None

    tier, similarity = await get_wire_tier(article, embedding, db)

    db_article = Article(
        url=article.url,
        outlet_id=article.outlet_id,
        title=article.title,
        summary=article.summary,
        body=article.body,
        author=article.author,
        language=article.language,
        published_at=article.published_at,
        collected_at=article.collected_at,
        collection_source=article.collection_source,
        wire_flag=False,  # activated in Phase 3 calibration
        wire_tier=tier if tier < 4 else None,
        embedding=embedding,
    )
    db.add(db_article)
    await db.flush()  # get the id without committing
    return db_article
