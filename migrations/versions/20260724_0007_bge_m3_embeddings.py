"""switch embeddings to bge-m3 (1024-dim) and add an HNSW index

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-24

The existing 384-dim vectors come from all-MiniLM-L6-v2 and are not convertible to
bge-m3's 1024-dim space, so the column is dropped and recreated empty. Run
`scripts/reembed.py` immediately after this migration to repopulate it — until then
every article has a NULL embedding and dedup/clustering will not match anything.

Also creates the ANN index that never existed: before this, every cosine_distance
query (clustering candidate search, dedup, wire-tier) was a sequential scan.
"""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0007"
down_revision: str = "0006"
branch_labels = None
depends_on = None

_INDEX = "articles_embedding_hnsw_idx"


def upgrade() -> None:
    op.drop_column("articles", "embedding")
    op.add_column("articles", sa.Column("embedding", Vector(1024), nullable=True))
    op.execute(f"CREATE INDEX {_INDEX} ON articles USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {_INDEX}")
    op.drop_column("articles", "embedding")
    op.add_column("articles", sa.Column("embedding", Vector(384), nullable=True))
