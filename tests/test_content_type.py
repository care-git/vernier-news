from sqlalchemy import select

from app.models.article import Article
from app.models.outlet import Outlet
from app.pipeline.dedup import detect_recurring


async def _outlet(db, domain: str) -> Outlet:
    outlet = Outlet(name=domain, domain=domain)
    db.add(outlet)
    await db.flush()
    return outlet


async def _article(db, outlet: Outlet, title: str, url: str) -> None:
    db.add(Article(url=url, outlet_id=outlet.id, title=title))
    await db.flush()


async def test_new_title_is_not_recurring(db):
    outlet = await _outlet(db, "new-title.example")

    assert await detect_recurring(outlet.id, "A story that has not run before", db) is False


async def test_repeated_title_from_same_outlet_is_recurring(db):
    outlet = await _outlet(db, "repeat.example")
    await _article(db, outlet, "Corrections and clarifications", "https://repeat.example/1")

    assert await detect_recurring(outlet.id, "Corrections and clarifications", db) is True


async def test_same_title_from_a_different_outlet_is_not_recurring(db):
    """Two outlets independently running the same headline is ordinary coverage."""
    first = await _outlet(db, "first.example")
    second = await _outlet(db, "second.example")
    await _article(db, first, "Meteor explodes over Massachusetts", "https://first.example/1")

    assert await detect_recurring(second.id, "Meteor explodes over Massachusetts", db) is False


async def test_content_type_defaults_to_none(db):
    """NULL content_type is what marks a record as a normal, clusterable story."""
    outlet = await _outlet(db, "default.example")
    await _article(db, outlet, "An ordinary story", "https://default.example/1")

    article = await db.scalar(select(Article).where(Article.url == "https://default.example/1"))

    assert article.content_type is None
