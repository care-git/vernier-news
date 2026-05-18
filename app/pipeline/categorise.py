from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


async def categorise_article(article_id: int, title: str, body: str, db: AsyncSession) -> None:
    """Call local Ollama (Mistral 7B) to classify the article into one or more categories.

    Updates the article's category_id in the database.
    """
    ...
