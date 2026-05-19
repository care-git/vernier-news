from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from sqlalchemy import select

from app.cache.clusters import precompute_cluster_summaries
from app.cache.digest import precompute_all_digests
from app.config import settings
from app.database import SessionLocal
from app.models.article import Article
from app.models.outlet import Outlet
from app.pipeline.categorise import categorise_article
from app.pipeline.clustering import assign_cluster, extract_entities, update_cluster_metadata
from app.pipeline.dedup import persist_article
from app.pipeline.ingestion.connectors import currents, gdelt, gnews, guardian, hackernews, nyt
from app.pipeline.ingestion.rss import ingest_feed, ingest_opml
from app.worker import celery_app

logger = logging.getLogger(__name__)

_OPML_PATH = str(Path(__file__).parent.parent.parent / "sources" / "feeds.opml")
_CATEGORISE_BATCH = 50  # articles per categorise_pending run


@celery_app.task(name="pipeline.ingest_feeds")
def ingest_feeds() -> dict:
    """Fetch all active RSS/Atom feeds and run each article through the pipeline."""

    async def _run() -> dict:
        async with SessionLocal() as db:
            # Build outlet_map {domain: id} for OPML domain resolution.
            outlet_rows = await db.execute(
                select(Outlet.domain, Outlet.id, Outlet.rss_feed_url).where(Outlet.active.is_(True))
            )
            all_outlets = outlet_rows.all()
            outlet_map = {r.domain: r.id for r in all_outlets}

            # Collect articles from OPML feeds.
            articles = ingest_opml(_OPML_PATH, outlet_map)

            # Also fetch outlets with rss_feed_url set that aren't covered by the OPML.
            opml_domains = {d for d, _ in outlet_map.items()}
            for outlet in all_outlets:
                if outlet.rss_feed_url and outlet.domain not in opml_domains:
                    articles.extend(ingest_feed(outlet.rss_feed_url, outlet.id))

            # API connectors — each skipped gracefully if key is absent.
            if settings.guardian_api_key:
                guardian_id = outlet_map.get("theguardian.com")
                if guardian_id:
                    articles.extend(await guardian.fetch(guardian_id, settings.guardian_api_key))

            if settings.nyt_api_key:
                nyt_id = outlet_map.get("nytimes.com")
                if nyt_id:
                    articles.extend(await nyt.fetch(nyt_id, settings.nyt_api_key))

            if settings.gnews_api_key:
                articles.extend(await gnews.fetch(outlet_map, settings.gnews_api_key))

            if settings.currents_api_key:
                articles.extend(await currents.fetch(outlet_map, settings.currents_api_key))

            # GDELT and HN require no API key.
            articles.extend(await gdelt.fetch(outlet_map))
            articles.extend(await hackernews.fetch(outlet_map))

            saved = 0
            for article in articles:
                try:
                    db_article = await persist_article(article, db)
                    if db_article is None:
                        continue

                    entities = extract_entities(f"{article.title} {article.body}")
                    cluster_id = await assign_cluster(
                        db_article.id,
                        db_article.embedding,
                        entities,
                        db_article.published_at,
                        db_article.wire_tier,
                        db,
                    )
                    await update_cluster_metadata(cluster_id, db)
                    saved += 1
                except Exception:
                    logger.exception("failed to process article: %s", article.url)

            await db.commit()
            logger.info("ingest_feeds: saved %d new articles", saved)
            return {"articles_saved": saved}

    return asyncio.run(_run())


@celery_app.task(name="pipeline.cluster_pass")
def cluster_pass() -> dict:
    """Assign any articles that were persisted without a cluster membership."""

    async def _run() -> dict:
        async with SessionLocal() as db:
            from sqlalchemy import exists, not_

            from app.models.cluster import ArticleCluster

            # Find articles with no cluster membership.
            result = await db.execute(
                select(Article)
                .where(Article.embedding.isnot(None))
                .where(
                    not_(
                        exists(
                            select(ArticleCluster.article_id).where(
                                ArticleCluster.article_id == Article.id
                            )
                        )
                    )
                )
                .limit(200)
            )
            articles = result.scalars().all()

            assigned = 0
            for article in articles:
                try:
                    text = f"{article.title} {article.body or ''}"
                    entities = extract_entities(text)
                    cluster_id = await assign_cluster(
                        article.id,
                        article.embedding,
                        entities,
                        article.published_at,
                        article.wire_tier,
                        db,
                    )
                    await update_cluster_metadata(cluster_id, db)
                    assigned += 1
                except Exception:
                    logger.exception("cluster_pass failed for article %d", article.id)

            await db.commit()
            logger.info("cluster_pass: assigned %d articles", assigned)
            return {"assigned": assigned}

    return asyncio.run(_run())


@celery_app.task(name="pipeline.categorise_pending")
def categorise_pending() -> dict:
    """Run Ollama categorisation on uncategorised articles."""

    async def _run() -> dict:
        async with SessionLocal() as db:
            result = await db.execute(
                select(Article)
                .where(Article.category_id == None)  # noqa: E711
                .where(Article.body.isnot(None))
                .order_by(Article.collected_at.desc())
                .limit(_CATEGORISE_BATCH)
            )
            articles = result.scalars().all()

            categorised = 0
            for article in articles:
                try:
                    await categorise_article(article.id, article.title, article.body or "", db)
                    categorised += 1
                except Exception:
                    logger.exception("categorisation failed for article %d", article.id)

            await db.commit()
            logger.info("categorise_pending: categorised %d articles", categorised)
            return {"categorised": categorised}

    return asyncio.run(_run())


@celery_app.task(name="pipeline.precompute_cluster_summaries")
def precompute_cluster_summaries_task() -> dict:
    """Pre-compute and cache cluster summary cards."""

    async def _run() -> dict:
        async with SessionLocal() as db:
            count = await precompute_cluster_summaries(db)
            return {"summaries_cached": count}

    return asyncio.run(_run())


@celery_app.task(name="pipeline.precompute_digests")
def precompute_digests() -> dict:
    """Pre-compute and cache digest payloads for all active user preference profiles."""

    async def _run() -> dict:
        async with SessionLocal() as db:
            count = await precompute_all_digests(db)
            return {"digests_cached": count}

    return asyncio.run(_run())
