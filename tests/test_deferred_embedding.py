from datetime import UTC, datetime

from sqlalchemy import select

from app.models.article import Article, ArticleSighting
from app.models.outlet import Outlet
from app.pipeline.dedup import is_duplicate, persist_article
from app.pipeline.ingestion.normalise import NormalisedArticle


async def _outlet(db, domain: str) -> Outlet:
    outlet = Outlet(name=domain, domain=domain)
    db.add(outlet)
    await db.flush()
    return outlet


def _incoming(outlet: Outlet, url: str, title: str = "A story") -> NormalisedArticle:
    now = datetime.now(UTC)
    return NormalisedArticle(
        url=url,
        outlet_id=outlet.id,
        title=title,
        body="",
        summary="",
        author=None,
        language="en",
        published_at=now,
        collected_at=now,
        collection_source="api:gdelt",
    )


async def test_deferred_article_is_stored_without_a_vector(db):
    """The historical backfill's whole affordability rests on this path."""
    outlet = await _outlet(db, "deferred.example")

    saved = await persist_article(_incoming(outlet, "https://deferred.example/1"), db, embed=False)
    await db.flush()

    assert saved is not None
    assert saved.embedding is None


async def test_deferred_article_has_no_wire_tier(db):
    """Wire tier is vector-derived, so NULL here means 'not computed', not 'original'."""
    outlet = await _outlet(db, "no-tier.example")

    saved = await persist_article(_incoming(outlet, "https://no-tier.example/1"), db, embed=False)
    await db.flush()

    assert saved.wire_tier is None


async def test_deferred_article_still_records_its_sighting(db):
    """Provenance capture must not depend on whether we chose to embed."""
    outlet = await _outlet(db, "sighted.example")

    saved = await persist_article(_incoming(outlet, "https://sighted.example/1"), db, embed=False)
    await db.flush()

    sightings = (
        (await db.execute(select(ArticleSighting).where(ArticleSighting.article_id == saved.id)))
        .scalars()
        .all()
    )

    assert len(sightings) == 1
    assert sightings[0].collection_source == "api:gdelt"


async def test_deferred_articles_are_invisible_to_clustering(db):
    """cluster_pass and recluster both filter on embedding IS NOT NULL."""
    outlet = await _outlet(db, "unclustered.example")
    await persist_article(_incoming(outlet, "https://unclustered.example/1"), db, embed=False)
    await db.flush()

    clusterable = (
        (
            await db.execute(
                select(Article.id)
                .where(Article.outlet_id == outlet.id)
                .where(Article.embedding.isnot(None))
            )
        )
        .scalars()
        .all()
    )

    assert clusterable == []


async def test_repeated_url_is_still_caught_without_a_vector(db):
    """Re-sweeping the same window must not duplicate rows."""
    outlet = await _outlet(db, "resweep.example")
    url = "https://resweep.example/1"
    await persist_article(_incoming(outlet, url), db, embed=False)
    await db.flush()

    again = await persist_article(_incoming(outlet, url), db, embed=False)

    assert again is None


async def test_is_duplicate_skips_the_vector_check_when_there_is_no_vector(db):
    outlet = await _outlet(db, "novector.example")
    db.add(Article(url="https://novector.example/1", outlet_id=outlet.id, title="Stored"))
    await db.flush()

    assert await is_duplicate("https://novector.example/1", None, db) is True
    assert await is_duplicate("https://novector.example/2", None, db) is False
