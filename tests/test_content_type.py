from sqlalchemy import select

from app.models.article import Article
from app.models.outlet import Outlet
from app.pipeline.dedup import (
    CONTENT_TYPE_DUPLICATE,
    CONTENT_TYPE_RECURRING,
    classify_repeat,
)
from app.pipeline.ingestion.normalise import canonical_path, normalise


async def _outlet(db, domain: str) -> Outlet:
    outlet = Outlet(name=domain, domain=domain)
    db.add(outlet)
    await db.flush()
    return outlet


async def _article(db, outlet: Outlet, title: str, url: str) -> None:
    db.add(Article(url=url, outlet_id=outlet.id, title=title))
    await db.flush()


def test_canonical_path_drops_host_and_query():
    """The two URL forms BBC content actually arrives under must collapse to one."""
    from_rss = "https://www.bbc.com/news/articles/c3ryw807133o?at_medium=RSS&at_campaign=rss"
    from_gnews = "https://www.bbc.co.uk/news/articles/c3ryw807133o"

    assert canonical_path(from_rss) == canonical_path(from_gnews)
    assert canonical_path(from_rss) == "/news/articles/c3ryw807133o"


def test_canonical_path_strips_trailing_slash_and_fragment_case():
    assert canonical_path("https://example.com/News/Story/") == "/news/story"


def test_canonical_path_keeps_distinct_paths_distinct():
    """NYT publishes one story under two section paths — genuinely different pages."""
    obituaries = "https://www.nytimes.com/2026/07/01/obituaries/victor-willis-dead.html"
    arts = "https://www.nytimes.com/2026/07/01/arts/music/victor-willis-dead.html"

    assert canonical_path(obituaries) != canonical_path(arts)


def test_normalise_collapses_internal_title_whitespace():
    raw = {"link": "https://example.com/a", "title": "  Corrections   and  clarifications "}

    article = normalise(raw, outlet_id=1, collection_source="test")

    assert article.title == "Corrections and clarifications"


async def test_unseen_headline_is_not_a_repeat(db):
    outlet = await _outlet(db, "new-title.example")

    assert await classify_repeat(outlet.id, "A story not run before", "/a", db) is None


async def test_same_headline_and_path_is_a_duplicate(db):
    """Same page, different URL form — the bbc.com / bbc.co.uk case."""
    outlet = await _outlet(db, "duplicate.example")
    await _article(
        db,
        outlet,
        "Nasa names next astronauts",
        "https://www.bbc.com/news/articles/abc123?at_medium=RSS",
    )

    verdict = await classify_repeat(
        outlet.id, "Nasa names next astronauts", "https://www.bbc.co.uk/news/articles/abc123", db
    )

    assert verdict == CONTENT_TYPE_DUPLICATE


async def test_same_headline_on_a_different_page_is_recurring(db):
    """The Guardian's corrections column: one standing headline, a new page each day."""
    outlet = await _outlet(db, "recurring.example")
    await _article(
        db,
        outlet,
        "Corrections and clarifications",
        "https://recurring.example/2026/jul/01/corrections",
    )

    verdict = await classify_repeat(
        outlet.id,
        "Corrections and clarifications",
        "https://recurring.example/2026/jul/02/corrections",
        db,
    )

    assert verdict == CONTENT_TYPE_RECURRING


async def test_same_headline_from_a_different_outlet_is_not_a_repeat(db):
    """Two outlets independently running one headline is ordinary coverage."""
    first = await _outlet(db, "first.example")
    second = await _outlet(db, "second.example")
    await _article(db, first, "Meteor explodes over Massachusetts", "https://first.example/1")

    verdict = await classify_repeat(
        second.id, "Meteor explodes over Massachusetts", "https://second.example/1", db
    )

    assert verdict is None


async def test_content_type_defaults_to_none(db):
    """NULL content_type is what marks a record as a normal, clusterable story."""
    outlet = await _outlet(db, "default.example")
    await _article(db, outlet, "An ordinary story", "https://default.example/1")

    article = await db.scalar(select(Article).where(Article.url == "https://default.example/1"))

    assert article.content_type is None
