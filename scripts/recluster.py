"""Wipe and rebuild every story cluster from scratch using the current clustering
settings, replaying articles in publication order — a faithful simulation of what
the live online clusterer now produces.

    make recluster
    # docker compose exec api python -m scripts.recluster

Use it to (a) collapse the legacy MiniLM-era fragmentation and (b) evaluate new
clustering settings: tweak a row in the `settings` table, re-run, and compare the
cluster-size distribution from `make analyse`.

DESTRUCTIVE: deletes every cluster and membership, then rebuilds. Safe *only* while
the digest is frozen and nothing depends on cluster IDs — do NOT run once users can
follow clusters/topics. Stop the worker first so live ingest doesn't race it:

    docker compose stop worker beat
    make recluster
    docker compose start worker beat
"""

from __future__ import annotations

import asyncio
import logging
import time

from sqlalchemy import delete, select

from app.database import SessionLocal
from app.models.article import Article
from app.models.cluster import ArticleCluster, Cluster
from app.pipeline import tuning
from app.pipeline.clustering import (
    assign_cluster,
    entities_from_mentions,
    extract_mentions,
    record_mentions,
    update_cluster_metadata,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("recluster")

_BATCH = 500


async def _rebuild(db) -> None:
    t = await tuning.refresh(db)
    logger.info(
        "settings: candidate_max_dist=%.2f  join_high=%.2f  join_mid=%.2f  "
        "entity_min=%.2f  entity_min_shared=%.0f",
        t.candidate_max_distance,
        t.join_semantic_high,
        t.join_semantic_mid,
        t.join_entity_min,
        t.join_entity_min_shared,
    )

    await db.execute(delete(ArticleCluster))
    await db.execute(delete(Cluster))
    await db.commit()
    logger.info("wiped existing clusters and memberships")

    # Publication order = the order the online clusterer would have seen them.
    # content_type is not NULL for recurring formats, which the live clusterer skips.
    ids = (
        (
            await db.execute(
                select(Article.id)
                .where(Article.embedding.isnot(None))
                .where(Article.content_type.is_(None))
                .order_by(Article.published_at.asc(), Article.id.asc())
            )
        )
        .scalars()
        .all()
    )
    logger.info("re-clustering %d articles in publication order", len(ids))

    start = time.time()
    done = 0
    for offset in range(0, len(ids), _BATCH):
        batch_ids = ids[offset : offset + _BATCH]
        rows = (
            await db.execute(
                select(
                    Article.id,
                    Article.embedding,
                    Article.title,
                    Article.body,
                    Article.published_at,
                    Article.wire_tier,
                ).where(Article.id.in_(batch_ids))
            )
        ).all()
        by_id = {r.id: r for r in rows}

        for article_id in batch_ids:  # preserve publication order within the batch
            r = by_id[article_id]
            mentions = extract_mentions(f"{r.title} {r.body or ''}")
            await record_mentions(r.id, mentions, db)
            entities = entities_from_mentions(mentions)
            # Metadata (counts, dormancy) is recomputed once at the end — skip per row.
            await assign_cluster(r.id, r.embedding, entities, r.published_at, r.wire_tier, db)

        await db.commit()
        done += len(batch_ids)
        rate = done / (time.time() - start)
        logger.info("clustered %d/%d  (%.0f/s)", done, len(ids), rate)

    # One metadata pass over the rebuilt clusters (source counts + dormancy).
    cluster_ids = (await db.execute(select(Cluster.id))).scalars().all()
    for cluster_id in cluster_ids:
        await update_cluster_metadata(cluster_id, db)
    await db.commit()

    n_clusters = len(cluster_ids)
    logger.info(
        "done: %d articles -> %d clusters (%.2f articles/cluster) in %.0fs",
        done,
        n_clusters,
        done / max(n_clusters, 1),
        time.time() - start,
    )
    logger.info("run `make analyse` for the full cluster-size distribution")


async def main() -> None:
    async with SessionLocal() as db:
        await _rebuild(db)


if __name__ == "__main__":
    asyncio.run(main())
