from __future__ import annotations

import json
import logging
import re

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.article import Article
from app.models.category import Category

logger = logging.getLogger(__name__)

_OLLAMA_TIMEOUT = 45.0

_PROMPT_TEMPLATE = """\
Classify the following news article into one or more of these categories.
Return ONLY a JSON array of slugs from the list below. No explanation.

Categories:
- politics
- economics
- technology
- science
- climate-environment
- health
- conflict-security
- society-culture
- business
- sport

Title: {title}
Text: {text}

JSON array:"""


def _parse_slugs(response: str) -> list[str]:
    """Extract a list of category slugs from the model response."""
    text = response.strip()

    # Happy path: the whole response is a JSON array.
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [s for s in parsed if isinstance(s, str)]
    except json.JSONDecodeError:
        pass

    # Fallback: extract the first [...] block in case the model added prose.
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, list):
                return [s for s in parsed if isinstance(s, str)]
        except json.JSONDecodeError:
            pass

    logger.warning("could not parse category slugs from model response: %r", text[:200])
    return []


async def _call_ollama(prompt: str) -> str | None:
    """POST to the Ollama generate endpoint and return the response text."""
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=_OLLAMA_TIMEOUT) as client:
            resp = await client.post(f"{settings.ollama_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "")
    except httpx.ConnectError:
        logger.warning(
            "Ollama not reachable at %s — article will remain uncategorised", settings.ollama_url
        )
    except httpx.TimeoutException:
        logger.warning("Ollama timed out after %.0fs", _OLLAMA_TIMEOUT)
    except Exception as exc:
        logger.error("Ollama call failed: %s", exc)
    return None


async def categorise_article(article_id: int, title: str, body: str, db: AsyncSession) -> None:
    """Call Ollama to classify the article and write category_id to the database.

    Fails gracefully: if Ollama is unavailable or returns unparseable output,
    the article remains uncategorised (category_id stays None).
    """
    # Load valid slugs from the database so we never assign a non-existent category.
    categories = await db.execute(select(Category.id, Category.slug))
    slug_to_id: dict[str, int] = {row.slug: row.id for row in categories.all()}

    if not slug_to_id:
        logger.error("no categories in database — run seed script first")
        return

    prompt = _PROMPT_TEMPLATE.format(
        title=title,
        text=body[:800],
    )

    response = await _call_ollama(prompt)
    if response is None:
        return

    slugs = _parse_slugs(response)
    valid = [s for s in slugs if s in slug_to_id]

    if not valid:
        logger.warning(
            "no valid category slugs in model response for article %d: %r", article_id, slugs
        )
        return

    # Assign the first valid category as the primary one for Phase 1.
    # Multi-category support (many-to-many) is a Phase 4 deliverable.
    category_id = slug_to_id[valid[0]]

    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        logger.error("article %d not found for categorisation", article_id)
        return

    article.category_id = category_id
    await db.flush()
    logger.debug("article %d categorised as '%s'", article_id, valid[0])
