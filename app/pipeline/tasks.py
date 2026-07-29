from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from sqlalchemy import func, select

from app.cache.clusters import precompute_cluster_summaries
from app.cache.digest import precompute_all_digests
from app.config import settings
from app.database import SessionLocal
from app.models.article import Article
from app.models.outlet import Outlet
from app.pipeline import tuning
from app.pipeline.categorise import categorise_article
from app.pipeline.clustering import assign_cluster, extract_entities, update_cluster_metadata
from app.pipeline.dedup import persist_article
from app.pipeline.ingestion.connectors import currents, gdelt, gnews, guardian, hackernews, nyt
from app.pipeline.ingestion.rss import ingest_feed, ingest_opml, parse_opml
from app.worker import celery_app

logger = logging.getLogger(__name__)

_OPML_PATH = str(Path(__file__).parent.parent.parent / "sources" / "feeds.opml")
_CATEGORISE_BATCH = 50  # articles per categorise_pending run


@celery_app.task(name="pipeline.ingest_feeds")
def ingest_feeds() -> dict:
    """Fetch all active RSS/Atom feeds and run each article through the pipeline."""

    async def _run() -> dict:
        async with SessionLocal() as db:
            await tuning.refresh(db)

            # Collect articles from OPML feeds, creating outlets for unknown domains.
            articles = await ingest_opml(_OPML_PATH, db)

            # Also fetch outlets carrying an rss_feed_url that the OPML does not cover.
            # The OPML domain set has to come from the file itself: deriving it from
            # the outlets table made the condition below always false, so this loop
            # silently never ran.
            opml_domains = {feed["domain"] for feed in parse_opml(_OPML_PATH)}
            outlet_rows = await db.execute(
                select(Outlet.domain, Outlet.id, Outlet.rss_feed_url).where(Outlet.active.is_(True))
            )
            all_outlets = outlet_rows.all()
            for outlet in all_outlets:
                if outlet.rss_feed_url and outlet.domain not in opml_domains:
                    articles.extend(ingest_feed(outlet.rss_feed_url, outlet.id))

            # Guardian and NYT are single-outlet connectors keyed on a seeded domain.
            outlet_map = {r.domain: r.id for r in all_outlets}

            # API connectors — each skipped gracefully if key is absent.
            if settings.guardian_api_key:
                guardian_id = outlet_map.get("theguardian.com")
                if guardian_id:
                    articles.extend(await guardian.fetch(guardian_id, settings.guardian_api_key))

            if settings.nyt_api_key:
                nyt_id = outlet_map.get("nytimes.com")
                if nyt_id:
                    articles.extend(await nyt.fetch(nyt_id, settings.nyt_api_key))

            # The aggregators span many publications, so they resolve outlets
            # themselves and create records for domains never seen before.
            if settings.gnews_api_key:
                articles.extend(await gnews.fetch(db, settings.gnews_api_key))

            if settings.currents_api_key:
                articles.extend(await currents.fetch(db, settings.currents_api_key))

            # HN requires no API key. GDELT has its own task — it sweeps time windows
            # on a much shorter cycle than the feeds can be politely polled on.
            articles.extend(await hackernews.fetch(db))

            saved = 0
            for article in articles:
                try:
                    db_article = await persist_article(article, db)
                    if db_article is None:
                        continue

                    # Recurring formats are stored but never story-clustered.
                    if db_article.content_type is None:
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


@celery_app.task(name="pipeline.sweep_gdelt")
def sweep_gdelt() -> dict:
    """Sweep GDELT forward in time windows, persisting and clustering what it finds.

    Separate from ingest_feeds because the two have opposite pacing needs: RSS feeds
    and the quota-limited APIs want polling every 30 minutes, while GDELT is the
    breadth source and wants sweeping as fast as its rate limit allows.
    """

    async def _run() -> dict:
        async with SessionLocal() as db:
            await tuning.refresh(db)

            # The cursor is the corpus itself: resume from the newest article GDELT has
            # given us. No extra state to keep in step with the data.
            since = await db.scalar(
                select(func.max(Article.published_at)).where(
                    Article.collection_source == "api:gdelt"
                )
            )
            articles = await gdelt.sweep(db, settings.gdelt_query, since)

            saved = 0
            for article in articles:
                try:
                    db_article = await persist_article(article, db)
                    if db_article is None:
                        continue
                    if db_article.content_type is None:
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
                    logger.exception("failed to process GDELT article: %s", article.url)

            await db.commit()
            logger.info("sweep_gdelt: saved %d new articles", saved)
            return {"articles_saved": saved}

    return asyncio.run(_run())


@celery_app.task(name="pipeline.cluster_pass")
def cluster_pass() -> dict:
    """Assign any articles that were persisted without a cluster membership."""

    async def _run() -> dict:
        async with SessionLocal() as db:
            await tuning.refresh(db)

            from sqlalchemy import exists, not_

            from app.models.cluster import ArticleCluster

            # Find articles with no cluster membership. Recurring formats are
            # deliberately unclustered, so they must not be picked up here.
            result = await db.execute(
                select(Article)
                .where(Article.embedding.isnot(None))
                .where(Article.content_type.is_(None))
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
