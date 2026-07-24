"""Re-embed articles that have no embedding, using the current embedding model.

Run this immediately after migration 0007, which drops the old 384-dim vectors:

    make reembed
    # equivalently: docker compose exec api python -m scripts.reembed

Must be invoked with `python -m` (not by file path) so that /app is on sys.path
and `app` is importable — same convention as scripts/seed.py.

Resumable: it only selects articles whose embedding IS NULL, so if it is
interrupted you can simply run it again and it picks up where it left off.

Run it in the `api` container with the worker stopped — that way only one process
holds the ~2GB model, and ingestion isn't racing the backfill.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.article import Article
from app.pipeline.embedding import embedding_text, generate_embeddings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("reembed")

_BATCH = 200


async def main() -> None:
    async with SessionLocal() as db:
        remaining = await db.scalar(
            select(func.count()).select_from(Article).where(Article.embedding.is_(None))
        )
        logger.info("articles needing embeddings: %d", remaining)
        if not remaining:
            return

        done = 0
        while True:
            result = await db.execute(
                select(Article).where(Article.embedding.is_(None)).limit(_BATCH)
            )
            articles = result.scalars().all()
            if not articles:
                break

            texts = [embedding_text(a.title, a.body) for a in articles]
            vectors = generate_embeddings(texts)
            for article, vector in zip(articles, vectors, strict=True):
                article.embedding = vector
            await db.commit()

            done += len(articles)
            logger.info("re-embedded %d / %d", done, remaining)

        logger.info("done — %d articles re-embedded", done)


if __name__ == "__main__":
    asyncio.run(main())
