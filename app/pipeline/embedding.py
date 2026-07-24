from __future__ import annotations

import logging

from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)

# Loaded once per process on first use (~2GB resident for bge-m3). Only processes
# that actually embed pay this cost — the API never calls into here.
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("loading embedding model %s", EMBEDDING_MODEL)
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def generate_embedding(text: str) -> list[float]:
    """Embed a single text, returning a normalised EMBEDDING_DIM-length vector."""
    return get_model().encode(text, normalize_embeddings=True).tolist()


def generate_embeddings(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Embed a batch of texts — used by the re-embed backfill."""
    vectors = get_model().encode(texts, normalize_embeddings=True, batch_size=batch_size)
    return [vector.tolist() for vector in vectors]


def embedding_text(title: str, body: str | None) -> str:
    """Build the text that gets embedded for an article.

    Kept in one place so the ingest path and the backfill always embed the same
    thing — otherwise re-embedded vectors would not be comparable to new ones.
    """
    return f"{title} {(body or '')[:500]}"
