"""add article_sightings — every URL form and collection path an article arrived under

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-27

One article reaches the pipeline under several URL forms: BBC RSS links to bbc.com
with campaign parameters while GNews returns the bare bbc.co.uk link, and the NYT API
varies the query string between sections. Until now the second form was discarded,
which for a news app is right and for a research tool is destroying evidence — how a
story propagates across paths and collection methods is itself the data.

This is the "list of syndication destinations" that CONCEPT.md §4 Stage 2 always
specified, and the mark-never-delete policy in docs/data-model.md.

The primary Article row keeps whichever form arrived first. Every form, including
that one, gets a row here, so "all URL forms for this article" is a single query.
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str = "0009"
branch_labels = None
depends_on = None

_TABLE = "article_sightings"
_INDEX = "ix_article_sightings_article_id"
_UNIQUE = "uq_article_sightings_article_url"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("article_id", sa.Integer, sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("collection_source", sa.Text),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("article_id", "url", name=_UNIQUE),
    )
    op.create_index(_INDEX, _TABLE, ["article_id"])


def downgrade() -> None:
    op.drop_index(_INDEX, table_name=_TABLE)
    op.drop_table(_TABLE)
