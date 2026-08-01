from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import spacy
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.cluster import ArticleCluster, Cluster
from app.models.entity import EntityMention
from app.pipeline import tuning

logger = logging.getLogger(__name__)

# Loaded once per worker process on first call.
_nlp: spacy.language.Language | None = None

# Entity types worth tracking for clustering purposes.
_ENTITY_LABELS = {"PERSON", "ORG", "GPE", "LOC", "EVENT", "NORP"}

# Clustering thresholds now live in the `settings` table — see app/pipeline/tuning.py.

# Wire tier → independence score mapping.
_TIER_INDEPENDENCE: dict[int | None, float] = {
    0: 0.0,
    1: 0.0,
    2: 0.25,
    3: 0.6,
    4: 1.0,
    None: 1.0,
}


def _get_nlp() -> spacy.language.Language:
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


# Leading titles/honorifics stripped so "President Trump" and "Trump" match.
_ENTITY_PREFIXES = ("the ", "mr ", "mrs ", "ms ", "dr ", "president ", "sir ", "prime minister ")


def _normalise_entity(entity: str) -> str:
    text = entity.strip().lower()
    for prefix in _ENTITY_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    return text


@dataclass(frozen=True)
class Mention:
    """One named entity as it appeared, at the position it appeared."""

    surface_form: str
    normalised: str
    label: str
    start_char: int


def extract_mentions(text: str) -> list[Mention]:
    """Run spaCy NER on the first 2000 chars and return every mention, with position.

    Repeats are kept: how often and where an entity is mentioned is signal in its own
    right, and it cannot be recovered once discarded. Clustering wants the deduplicated
    view instead — see extract_entities.
    """
    doc = _get_nlp()(text[:2000])
    return [
        Mention(
            surface_form=ent.text.strip(),
            normalised=_normalise_entity(ent.text),
            label=ent.label_,
            start_char=ent.start_char,
        )
        for ent in doc.ents
        if ent.label_ in _ENTITY_LABELS and len(ent.text.strip()) > 2
    ]


def entities_from_mentions(mentions: list[Mention]) -> list[str]:
    """Deduplicated surface forms, which is what the cluster entity cache compares on.

    Callers that also persist mentions should extract once and use this, rather than
    calling extract_entities and paying for a second spaCy pass over the same text.
    """
    seen: set[str] = set()
    entities: list[str] = []
    for mention in mentions:
        key = mention.surface_form.lower()
        if key not in seen:
            seen.add(key)
            entities.append(mention.surface_form)
    return entities


def extract_entities(text: str) -> list[str]:
    """Run spaCy NER on the first 2000 chars and return deduplicated entity strings."""
    return entities_from_mentions(extract_mentions(text))


def _entity_overlap(a: list[str], b: list[str]) -> tuple[float, int]:
    """Return the overlap coefficient |A∩B| / min(|A|,|B|) and the shared-entity count.

    Overlap coefficient rather than Jaccard so a short entity list shared with a
    longer one isn't penalised by the union size — the old Jaccard term was
    systematically low and dragged genuinely related articles below threshold.

    The coefficient alone is not enough, which is why the count comes back with it.
    Dividing by the smaller set means the incoming article's entity count is almost
    always the denominator, so a single shared name clears 0.30 whenever the article
    has three or fewer entities — and the cluster side of the comparison accumulates
    every entity it has ever seen, so the chance of sharing *something* rises with
    cluster size. Callers require a minimum absolute count as well.
    """
    set_a = {_normalise_entity(e) for e in a} - {""}
    set_b = {_normalise_entity(e) for e in b} - {""}
    if not set_a or not set_b:
        return 0.0, 0
    shared = len(set_a & set_b)
    return shared / min(len(set_a), len(set_b)), shared


async def record_mentions(article_id: int, mentions: list[Mention], db: AsyncSession) -> None:
    """Persist an article's entity mentions, replacing any already held for it.

    Replace rather than append so re-running extraction over an article — after a
    model upgrade, or during a rebuild — converges instead of accumulating duplicates.
    """
    await db.execute(delete(EntityMention).where(EntityMention.article_id == article_id))
    db.add_all(
        [
            EntityMention(
                article_id=article_id,
                surface_form=mention.surface_form,
                normalised=mention.normalised,
                label=mention.label,
                start_char=mention.start_char,
            )
            for mention in mentions
        ]
    )


async def assign_cluster(
    article_id: int,
    embedding: list[float],
    entities: list[str],
    published_at: datetime,
    wire_tier: int | None,
    db: AsyncSession,
) -> int:
    """Assign the article to the best matching active cluster, or create a new one.

    Semantic-primary scoring: iterating candidate clusters closest-first, join the
    first whose nearest-member similarity is >= join_semantic_high, or is
    >= join_semantic_mid with entity overlap >= join_entity_min. Otherwise seed a
    new cluster.

    Returns the cluster_id.
    """
    t = tuning.current()
    cutoff = (published_at or datetime.now(UTC)) - timedelta(hours=t.temporal_window_hours)

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
        .where(Article.embedding.cosine_distance(embedding) < t.candidate_max_distance)
        .group_by(ArticleCluster.cluster_id, Cluster.entity_cache)
        .order_by("min_dist")
        .limit(10)
    )
    rows = candidates.all()

    best_cluster_id: int | None = None
    best_score = 0.0

    # Candidates are ordered closest-first; take the first that clears the join rule.
    for row in rows:
        semantic_score = 1.0 - row.min_dist
        if semantic_score < t.join_semantic_mid:
            break  # remaining candidates are only further away — none can qualify
        overlap, shared = _entity_overlap(entities, row.entity_cache or [])
        entity_corroborated = shared >= t.join_entity_min_shared and overlap >= t.join_entity_min
        if semantic_score >= t.join_semantic_high or entity_corroborated:
            best_cluster_id = row.cluster_id
            best_score = semantic_score
            break

    if best_cluster_id is None:
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
        cluster_result = await db.execute(select(Cluster).where(Cluster.id == best_cluster_id))
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
    db.add(
        ArticleCluster(
            article_id=article_id,
            cluster_id=best_cluster_id,
            independence_score=independence,
        )
    )

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
        age = datetime.now(UTC) - row.last_joined.replace(tzinfo=UTC)
        if age > timedelta(hours=tuning.current().dormancy_hours):
            cluster.active = False

    await db.flush()
