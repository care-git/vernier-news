from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import feedparser
from sqlalchemy.ext.asyncio import AsyncSession

from app.pipeline.ingestion.normalise import NormalisedArticle, domain_from_url, normalise
from app.pipeline.ingestion.outlets import resolve_outlet

logger = logging.getLogger(__name__)


def parse_opml(opml_path: str) -> list[dict]:
    """Parse an OPML file and return feed descriptors.

    Each descriptor is: {url, domain, name}
    Domain is used at call time to look up outlet_id from the database.
    """
    try:
        tree = ET.parse(opml_path)
    except (ET.ParseError, FileNotFoundError) as exc:
        logger.error("Failed to parse OPML file %s: %s", opml_path, exc)
        return []

    feeds = []
    for outline in tree.getroot().iter("outline"):
        xml_url = outline.get("xmlUrl", "").strip()
        if not xml_url:
            continue

        # Prefer explicit domain attribute; fall back to deriving it from htmlUrl
        domain = outline.get("domain", "").strip()
        if not domain:
            html_url = outline.get("htmlUrl", "")
            domain = domain_from_url(html_url) if html_url else ""

        if not domain:
            logger.warning("OPML entry missing domain, skipping: %s", xml_url)
            continue

        feeds.append(
            {
                "url": xml_url,
                "domain": domain,
                "name": outline.get("text") or outline.get("title") or xml_url,
            }
        )

    return feeds


def ingest_feed(feed_url: str, outlet_id: int) -> list[NormalisedArticle]:
    """Fetch and parse a single RSS/Atom feed, returning normalised articles.

    feedparser.parse() is synchronous and runs fine inside Celery workers.
    """
    try:
        parsed = feedparser.parse(feed_url)
    except Exception as exc:
        logger.error("Failed to fetch feed %s: %s", feed_url, exc)
        return []

    if parsed.get("bozo") and not parsed.entries:
        logger.warning(
            "Malformed feed or fetch error for %s: %s", feed_url, parsed.get("bozo_exception")
        )
        return []

    articles = []
    for entry in parsed.entries:
        article = normalise(entry, outlet_id, collection_source=f"rss:{feed_url}")
        if article is not None:
            articles.append(article)

    logger.info("Fetched %d articles from %s", len(articles), feed_url)
    return articles


async def ingest_opml(opml_path: str, db: AsyncSession) -> list[NormalisedArticle]:
    """Fetch every feed in an OPML file, creating outlets for domains not yet known.

    Feeds used to be skipped when their domain was missing from the outlets table,
    which made adding a source a two-step job — seed the outlet, then add the feed —
    with silent failure if you did only the second. The OPML entry carries a display
    name, so outlets discovered this way are better labelled than those found through
    the aggregator APIs.
    """
    articles: list[NormalisedArticle] = []

    for feed in parse_opml(opml_path):
        outlet_id = await resolve_outlet(feed["domain"], db, name=feed["name"])
        if outlet_id is None:
            logger.warning("Could not resolve an outlet for feed %s", feed["url"])
            continue
        articles.extend(ingest_feed(feed["url"], outlet_id))

    return articles
