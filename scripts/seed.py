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
OUTLETS = [
    ("BBC News", "bbc.co.uk", "GB", "en", 0.0, "MBFC"),
    ("Reuters", "reuters.com", "GB", "en", 0.0, "MBFC"),
    ("Associated Press", "apnews.com", "US", "en", 0.0, "MBFC"),
    ("Al Jazeera English", "aljazeera.com", "QA", "en", -0.1, "MBFC"),
    ("The Guardian", "theguardian.com", "GB", "en", -0.35, "MBFC"),
    ("The New York Times", "nytimes.com", "US", "en", -0.25, "MBFC"),
    ("The Washington Post", "washingtonpost.com", "US", "en", -0.25, "MBFC"),
    ("The Wall Street Journal", "wsj.com", "US", "en", 0.2, "MBFC"),
    ("Fox News", "foxnews.com", "US", "en", 0.55, "MBFC"),
    ("MSNBC", "msnbc.com", "US", "en", -0.5, "MBFC"),
    ("CNN", "cnn.com", "US", "en", -0.2, "MBFC"),
    ("The Economist", "economist.com", "GB", "en", 0.1, "MBFC"),
    ("Financial Times", "ft.com", "GB", "en", 0.1, "MBFC"),
    ("Der Spiegel", "spiegel.de", "DE", "de", -0.2, "MBFC"),
    ("Le Monde", "lemonde.fr", "FR", "fr", -0.15, "MBFC"),
    ("El País", "elpais.com", "ES", "es", -0.15, "MBFC"),
    ("NHK World", "nhk.or.jp", "JP", "en", 0.0, "MBFC"),
    ("France 24", "france24.com", "FR", "en", 0.0, "MBFC"),
    ("Deutsche Welle", "dw.com", "DE", "en", 0.0, "MBFC"),
    ("The Times", "thetimes.co.uk", "GB", "en", 0.2, "MBFC"),
    ("The Daily Telegraph", "telegraph.co.uk", "GB", "en", 0.4, "MBFC"),
    ("The Independent", "independent.co.uk", "GB", "en", -0.15, "MBFC"),
    ("The Spectator", "spectator.co.uk", "GB", "en", 0.45, "MBFC"),
    ("New Statesman", "newstatesman.com", "GB", "en", -0.4, "MBFC"),
    ("ProPublica", "propublica.org", "US", "en", -0.3, "MBFC"),
    ("The Intercept", "theintercept.com", "US", "en", -0.55, "MBFC"),
    ("Axios", "axios.com", "US", "en", 0.0, "MBFC"),
    ("Politico", "politico.com", "US", "en", -0.05, "MBFC"),
    ("Bloomberg", "bloomberg.com", "US", "en", 0.05, "MBFC"),
    ("Vice News", "vice.com", "US", "en", -0.4, "MBFC"),
]


async def seed() -> None:
    async with SessionLocal() as db:
        # Categories
        for name, slug in CATEGORIES:
            existing = await db.execute(select(Category).where(Category.slug == slug))
            if existing.scalar_one_or_none() is None:
                db.add(Category(name=name, slug=slug))

        # Outlets
        for name, domain, country, lang, leaning, source in OUTLETS:
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
                        active=True,
                    )
                )

        await db.commit()
        print(f"Seeded {len(CATEGORIES)} categories and {len(OUTLETS)} outlets.")


if __name__ == "__main__":
    asyncio.run(seed())
