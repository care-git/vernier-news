"""
Seed the database with initial categories and a starter outlet list.

Usage: python -m scripts.seed
"""

import asyncio

from sqlalchemy import select

from app.database import SessionLocal
from app.models.category import Category
from app.models.outlet import Outlet

CATEGORIES = [
    ("Politics", "politics"),
    ("Economics", "economics"),
    ("Technology", "technology"),
    ("Science", "science"),
    ("Climate & Environment", "climate-environment"),
    ("Health", "health"),
    ("Conflict & Security", "conflict-security"),
    ("Society & Culture", "society-culture"),
    ("Business", "business"),
    ("Sport", "sport"),
]

# Starter outlet list — political_leaning_lr sourced from MBFC public dataset
# Scale: -1.0 (far left) to 1.0 (far right); 0.0 = centre
# rss_feed_url: main feed URL where confirmed; None where unverified (add via feeds.opml or update later)
OUTLETS = [
    ("BBC News", "bbc.co.uk", "GB", "en", 0.0, "MBFC", "https://feeds.bbci.co.uk/news/rss.xml"),
    ("Reuters", "reuters.com", "GB", "en", 0.0, "MBFC", None),
    ("Associated Press", "apnews.com", "US", "en", 0.0, "MBFC", None),
    ("Al Jazeera English", "aljazeera.com", "QA", "en", -0.1, "MBFC", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("The Guardian", "theguardian.com", "GB", "en", -0.35, "MBFC", "https://www.theguardian.com/world/rss"),
    ("The New York Times", "nytimes.com", "US", "en", -0.25, "MBFC", None),
    ("The Washington Post", "washingtonpost.com", "US", "en", -0.25, "MBFC", None),
    ("The Wall Street Journal", "wsj.com", "US", "en", 0.2, "MBFC", None),
    ("Fox News", "foxnews.com", "US", "en", 0.55, "MBFC", None),
    ("MSNBC", "msnbc.com", "US", "en", -0.5, "MBFC", None),
    ("CNN", "cnn.com", "US", "en", -0.2, "MBFC", None),
    ("The Economist", "economist.com", "GB", "en", 0.1, "MBFC", None),
    ("Financial Times", "ft.com", "GB", "en", 0.1, "MBFC", None),
    ("Der Spiegel", "spiegel.de", "DE", "de", -0.2, "MBFC", None),
    ("Le Monde", "lemonde.fr", "FR", "fr", -0.15, "MBFC", None),
    ("El País", "elpais.com", "ES", "es", -0.15, "MBFC", None),
    ("NHK World", "nhk.or.jp", "JP", "en", 0.0, "MBFC", None),
    ("France 24", "france24.com", "FR", "en", 0.0, "MBFC", "https://www.france24.com/en/rss"),
    ("Deutsche Welle", "dw.com", "DE", "en", 0.0, "MBFC", "https://rss.dw.com/rdf/rss-en-all"),
    ("The Times", "thetimes.co.uk", "GB", "en", 0.2, "MBFC", None),
    ("The Daily Telegraph", "telegraph.co.uk", "GB", "en", 0.4, "MBFC", None),
    ("The Independent", "independent.co.uk", "GB", "en", -0.15, "MBFC", None),
    ("The Spectator", "spectator.co.uk", "GB", "en", 0.45, "MBFC", None),
    ("New Statesman", "newstatesman.com", "GB", "en", -0.4, "MBFC", None),
    ("ProPublica", "propublica.org", "US", "en", -0.3, "MBFC", "https://feeds.propublica.org/propublica/main"),
    ("The Intercept", "theintercept.com", "US", "en", -0.55, "MBFC", "https://theintercept.com/feed/?rss"),
    ("Axios", "axios.com", "US", "en", 0.0, "MBFC", None),
    ("Politico", "politico.com", "US", "en", -0.05, "MBFC", None),
    ("Bloomberg", "bloomberg.com", "US", "en", 0.05, "MBFC", None),
    ("Vice News", "vice.com", "US", "en", -0.4, "MBFC", None),
    ("Hacker News", "news.ycombinator.com", "US", "en", 0.0, None, None),
]


async def seed() -> None:
    async with SessionLocal() as db:
        # Categories
        for name, slug in CATEGORIES:
            existing = await db.execute(select(Category).where(Category.slug == slug))
            if existing.scalar_one_or_none() is None:
                db.add(Category(name=name, slug=slug))

        # Outlets
        for name, domain, country, lang, leaning, source, rss_feed_url in OUTLETS:
            existing = await db.execute(select(Outlet).where(Outlet.domain == domain))
            if existing.scalar_one_or_none() is None:
                db.add(
                    Outlet(
                        name=name,
                        domain=domain,
                        country=country,
                        language_primary=lang,
                        political_leaning_lr=leaning,
                        political_leaning_source=source,
                        rss_feed_url=rss_feed_url,
                        active=True,
                    )
                )

        await db.commit()
        print(f"Seeded {len(CATEGORIES)} categories and {len(OUTLETS)} outlets.")


if __name__ == "__main__":
    asyncio.run(seed())
