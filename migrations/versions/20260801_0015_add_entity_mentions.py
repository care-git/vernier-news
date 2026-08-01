"""add entity_mentions — persist the NER output already computed at ingest

Revision ID: 0015
Revises: 0014
Create Date: 2026-08-01

spaCy runs over every article at ingest, but its output was collapsed into a cluster's
entity_cache and the per-article detail discarded. Storing it costs a table and no
extra compute; recovering it later would mean re-running NER over the whole corpus,
and the cost of that grows with every article ingested.

Deliberately unresolved: no entity_id, because linking surface forms to canonical
Wikidata identities is Phase 4 (CONCEPT.md §10), and an entities table built before
the resolution method exists would fix the wrong shape. `normalised` is the interim
grouping key and is indexed for it.
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str = "0014"
branch_labels = None
depends_on = None

_TABLE = "entity_mentions"
_ARTICLE_INDEX = "ix_entity_mentions_article_id"
_NORMALISED_INDEX = "ix_entity_mentions_normalised"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("article_id", sa.Integer, sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("surface_form", sa.Text, nullable=False),
        sa.Column("normalised", sa.Text, nullable=False),
        sa.Column("label", sa.String(16), nullable=False),
        sa.Column("start_char", sa.Integer, nullable=False),
    )
    op.create_index(_ARTICLE_INDEX, _TABLE, ["article_id"])
    op.create_index(_NORMALISED_INDEX, _TABLE, ["normalised"])


def downgrade() -> None:
    op.drop_index(_NORMALISED_INDEX, table_name=_TABLE)
    op.drop_index(_ARTICLE_INDEX, table_name=_TABLE)
    op.drop_table(_TABLE)
