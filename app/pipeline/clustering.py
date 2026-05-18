from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import spacy
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.cluster import ArticleCluster, Cluster

logger = logging.getLogger(__name__)

# Loaded once per worker process on first call.
_nlp: spacy.language.Language | None = None

# Entity types worth tracking for clustering purposes.
_ENTITY_LABELS = {"PERSON", "ORG", "GPE", "LOC", "EVENT", "NORP"}

# Clustering thresholds — moved to DB settings table in Phase 3.
_CANDIDATE_MAX_DISTANCE = 0.6    # similarity > 0.4 to be a candidate cluster
_COMBINED_SCORE_THRESHOLD = 0.45
_SEMANTIC_WEIGHT = 0.6
_ENTITY_WEIGHT = 0.4
_TEMPORAL_WINDOW_HOURS = 72
_DORMANCY_HOURS = 48

# Wire tier → independence score mapping.
_TIER_INDEPENDENCE: dict[int | None, float] = {
    0: 0.0, 1: 0.0, 2: 0.25, 3: 0.6, 4: 1.0, None: 1.0,
}


def _get_nlp() -> spacy.language.Language:
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def extract_entities(text: str) -> list[str]:
    """Run spaCy NER on the first 2000 chars and return deduplicated entity strings."""
    doc = _get_nlp()(text[:2000])
    seen: set[str] = set()
    entities: list[str] = []
    for ent in doc.ents:
        if ent.label_ not in _ENTITY_LABELS:
            continue
        normalised = ent.text.strip().lower()
        if len(normalised) > 2 and normalised not in seen:
            seen.add(normalised)
            entities.append(ent.text.strip())
    return entities


def _jaccard(a: list[str], b: list[str]) -> float:
    set_a = {e.lower() for e in a}
    set_b = {e.lower() for e in b}
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


async def assign_cluster(
    article_id: int,
    embedding: list[float],
    entities: list[str],
    published_at: datetime,
    wire_tier: int | None,
    db: AsyncSession,
) -> int:
    """Assign the article to the best matching active cluster, or create a new one.

    Scoring: combined = 0.6 * semantic_similarity + 0.4 * entity_jaccard
    An article joins a cluster when combined >= 0.45.

    Returns the cluster_id.
    """
    cutoff = (published_at or datetime.now(timezone.utc)) - timedelta(hours=_TEMPORAL_WINDOW_HOURS)

    # Find active clusters with at least one semantically close article in the window.
    candidates = await db.execute(
        select(
            ArticleCluster.cluster_id,
            func.min(Article.embedding.cosine_distance(embedding)).label("min_dist"),
            Cluster.entity_cache,
        )
        .join(Article, Article.id == ArticleCluster.article_id)
        .join(Cluster, Cluster.id == ArticleCluster.cluster_id)
        .where(Cluster.active == True)  # noqa: E712
        .where(Article.published_at >= cutoff)
        .where(Article.embedding.isnot(None))
        .where(Article.embedding.cosine_distance(embedding) < _CANDIDATE_MAX_DISTANCE)
        .group_by(ArticleCluster.cluster_id, Cluster.entity_cache)
        .order_by("min_dist")
        .limit(10)
    )
    rows = candidates.all()

    best_cluster_id: int | None = None
    best_score = 0.0

    for row in rows:
        semantic_score = 1.0 - row.min_dist
        entity_score = _jaccard(entities, row.entity_cache or [])
        combined = _SEMANTIC_WEIGHT * semantic_score + _ENTITY_WEIGHT * entity_score

        if combined > best_score:
            best_score = combined
            best_cluster_id = row.cluster_id

    if best_cluster_id is None or best_score < _COMBINED_SCORE_THRESHOLD:
        # No suitable cluster — seed a new one.
        cluster = Cluster(
            first_published_at=published_at,
            entity_cache=entities,
            total_source_count=0,
            independent_source_count=0,
            active=True,
        )
        db.add(cluster)
        await db.flush()
        best_cluster_id = cluster.id
        logger.debug("new cluster %d seeded for article %d", best_cluster_id, article_id)
    else:
        # Merge entity cache with the new article's entities.
        cluster_result = await db.execute(
            select(Cluster).where(Cluster.id == best_cluster_id)
        )
        cluster = cluster_result.scalar_one()
        existing = set(e.lower() for e in (cluster.entity_cache or []))
        merged = list(cluster.entity_cache or []) + [
            e for e in entities if e.lower() not in existing
        ]
        cluster.entity_cache = merged
        logger.debug(
            "article %d joined cluster %d (score=%.3f)", article_id, best_cluster_id, best_score
        )

    independence = _TIER_INDEPENDENCE[wire_tier]
    db.add(ArticleCluster(
        article_id=article_id,
        cluster_id=best_cluster_id,
        independence_score=independence,
    ))

    await db.flush()
    return best_cluster_id


async def update_cluster_metadata(cluster_id: int, db: AsyncSession) -> None:
    """Recompute source counts and dormancy status for a cluster."""
    cluster_result = await db.execute(select(Cluster).where(Cluster.id == cluster_id))
    cluster = cluster_result.scalar_one_or_none()
    if cluster is None:
        return

    counts = await db.execute(
        select(
            func.count(ArticleCluster.article_id).label("total"),
            func.sum(ArticleCluster.independence_score).label("independent"),
            func.max(ArticleCluster.joined_at).label("last_joined"),
        ).where(ArticleCluster.cluster_id == cluster_id)
    )
    row = counts.one()

    cluster.total_source_count = row.total or 0
    cluster.independent_source_count = round(row.independent or 0)

    if row.last_joined:
        age = datetime.now(timezone.utc) - row.last_joined.replace(tzinfo=timezone.utc)
        if age > timedelta(hours=_DORMANCY_HOURS):
            cluster.active = False

    await db.flush()
