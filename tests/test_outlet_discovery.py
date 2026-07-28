from sqlalchemy import select

from app.models.outlet import Outlet
from app.pipeline.ingestion.normalise import domain_from_url
from app.pipeline.ingestion.outlets import country_code, resolve_outlet


def test_country_code_maps_names_and_codes_alike():
    """GDELT reports a country name; other connectors may send a code already."""
    assert country_code("United Kingdom") == "GB"
    assert country_code("GB") == "GB"
    assert country_code("gbr") == "GB"
    assert country_code("Qatar") == "QA"


def test_country_code_returns_none_rather_than_guessing():
    """A wrong country silently corrupts coverage distribution, which is per-region."""
    assert country_code("Nowhereland") is None
    assert country_code("") is None
    assert country_code(None) is None


def test_domain_from_url_strips_www_and_lowercases():
    assert domain_from_url("https://WWW.BBC.co.uk/news/articles/abc") == "bbc.co.uk"


def test_domain_from_url_keeps_distinct_hosts_distinct():
    """bbc.com and bbc.co.uk are one outlet, but that is resolved by seeding, not here."""
    assert domain_from_url("https://www.bbc.com/x") != domain_from_url("https://www.bbc.co.uk/x")


async def test_existing_outlet_is_reused_not_duplicated(db):
    seeded = Outlet(name="Seeded News", domain="seeded.example", political_leaning_lr=-0.2)
    db.add(seeded)
    await db.flush()

    resolved = await resolve_outlet("seeded.example", db)

    assert resolved == seeded.id


async def test_unknown_domain_creates_a_discovered_outlet(db):
    """The aggregation inversion: articles bring their sources with them."""
    outlet_id = await resolve_outlet("newspaper.example", db)
    await db.flush()

    outlet = await db.scalar(select(Outlet).where(Outlet.id == outlet_id))

    assert outlet.domain == "newspaper.example"
    assert outlet.name == "newspaper.example"
    assert outlet.discovered_at is not None
    assert outlet.active is True
    assert outlet.wire_service is False


async def test_discovered_outlet_records_a_mapped_country(db):
    outlet_id = await resolve_outlet(
        "gdelt-found.example", db, name="Found News", country="United Kingdom"
    )
    await db.flush()

    outlet = await db.scalar(select(Outlet).where(Outlet.id == outlet_id))

    assert outlet.country == "GB"
    assert outlet.name == "Found News"


async def test_discovered_outlet_has_no_political_leaning(db):
    """Leaning is computed, never invented at discovery time."""
    outlet_id = await resolve_outlet("unleaned.example", db)
    await db.flush()

    outlet = await db.scalar(select(Outlet).where(Outlet.id == outlet_id))

    assert outlet.political_leaning_lr is None
    assert outlet.political_leaning_source is None


async def test_seeded_outlets_are_distinguishable_from_discovered_ones(db):
    """discovered_at is the collection-asymmetry metadata a researcher needs."""
    db.add(Outlet(name="Curated", domain="curated.example", political_leaning_source="MBFC"))
    await db.flush()
    await resolve_outlet("found.example", db)
    await db.flush()

    curated = await db.scalar(select(Outlet).where(Outlet.domain == "curated.example"))
    found = await db.scalar(select(Outlet).where(Outlet.domain == "found.example"))

    assert curated.discovered_at is None
    assert found.discovered_at is not None


async def test_empty_domain_resolves_to_nothing(db):
    """An article with no resolvable source has no provenance and cannot be cited."""
    assert await resolve_outlet("", db) is None


async def test_resolve_is_idempotent_for_the_same_domain(db):
    first = await resolve_outlet("repeat.example", db)
    await db.flush()
    second = await resolve_outlet("repeat.example", db)
    await db.flush()

    rows = (
        (await db.execute(select(Outlet.id).where(Outlet.domain == "repeat.example")))
        .scalars()
        .all()
    )

    assert first == second
    assert len(rows) == 1
