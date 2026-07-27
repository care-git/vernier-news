from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article, ArticleSighting
from app.models.outlet import Outlet
from app.pipeline import tuning
from app.pipeline.embedding import embedding_text, generate_embedding
from app.pipeline.ingestion.normalise import NormalisedArticle, canonical_path

logger = logging.getLogger(__name__)

# Wire tier + dedup thresholds now live in the `settings` table — see
# app/pipeline/tuning.py. The embedding model lives in app/pipeline/embedding.py.

# Article.content_type values (migration 0009). NULL means a normal one-off story —
# the only kind that gets story-clustered.
#
# A recurring format reuses one headline indefinitely on a *new* page each time: the
# Guardian's daily corrections column, World Cup fixture listings, live-briefing
# stubs, radio-programme entries. Kept — the corrections column feeds the
# correction-record dimension of the feature analysis system — but not clustered,
# since grouping months of instalments under one headline is not a story.
CONTENT_TYPE_RECURRING = "recurring"
# The same page reaching us twice under URL forms too different for the URL and
# embedding checks below to catch. The live pipeline never stores a second Article row
# for these — it files the URL form as a sighting against the one already held — so
# this value only ever labels the backlog collected before sightings existed.
CONTENT_TYPE_DUPLICATE = "duplicate"


async def classify_repeat(
    outlet_id: int, title: str, url: str, db: AsyncSession
) -> tuple[str | None, int | None]:
    """Classify an incoming article against this outlet's identical past headlines.

    Body length cannot separate these from real coverage — roughly a third of the
    corpus is summary-only, including outlets that cluster well — but an exact
    headline repeat from the same outlet is a reliable signal, and the URL path then
    says which kind of repeat it is.

    Returns ``(content_type, duplicate_of)``:
        (None, None)                    — a headline this outlet has not run before
        (CONTENT_TYPE_DUPLICATE, id)    — the same page already stored under another
                                          URL form; ``id`` is the article to record
                                          this URL form against
        (CONTENT_TYPE_RECURRING, None)  — the same headline on a genuinely different page
    """
    result = await db.execute(
        select(Article.id, Article.url)
        .where(Article.outlet_id == outlet_id)
        .where(Article.title == title)
    )
    existing = result.all()
    if not existing:
        return None, None

    path = canonical_path(url)
    for article_id, seen_url in existing:
        if canonical_path(seen_url) == path:
            return CONTENT_TYPE_DUPLICATE, article_id
    return CONTENT_TYPE_RECURRING, None


async def record_sighting(
    article_id: int, url: str, collection_source: str | None, db: AsyncSession
) -> None:
    """Record that this article was observed at this URL, via this collection path.

    Idempotent per (article_id, url), so a feed re-listing an unchanged URL adds
    nothing. Deliberately not called from is_duplicate()'s near-identical-embedding
    branch: that match can span outlets, which is wire syndication rather than another
    URL form of the same article, and conflating the two would corrupt both.
    """
    await db.execute(
        pg_insert(ArticleSighting)
        .values(article_id=article_id, url=url, collection_source=collection_source)
        .on_conflict_do_nothing(index_elements=["article_id", "url"])
    )


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
        1. Classify against this outlet's identical past headlines. If the same page is
           already stored under a different URL form, record the form as a sighting
           against it and return None — no second Article row.
        2. Generate embedding from title + body excerpt
        3. Check for exact URL duplicate or near-identical content (returns None if found)
        4. Compute and log wire tier (Phase 1: log only, no collapsing)
        5. Write Article record to the database, flagging recurring formats so the
           caller can skip story clustering, and record its own URL as a sighting

    Returns the saved Article ORM object, or None if the article was a duplicate.
    """
    # First, because it is a cheap indexed lookup that can spare us an embedding.
    content_type, duplicate_of = await classify_repeat(
        article.outlet_id, article.title, article.url, db
    )
    if content_type == CONTENT_TYPE_DUPLICATE:
        await record_sighting(duplicate_of, article.url, article.collection_source, db)
        logger.debug(
            "duplicate URL form recorded against article %d: %s", duplicate_of, article.url
        )
        return None
    if content_type == CONTENT_TYPE_RECURRING:
        logger.info("recurring format (not clustered): %s — %s", article.title, article.url)

    embedding = generate_embedding(embedding_text(article.title, article.body))

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
        content_type=content_type,
        embedding=embedding,
    )
    db.add(db_article)
    await db.flush()  # get the id without committing
    await record_sighting(db_article.id, article.url, article.collection_source, db)
    return db_article
