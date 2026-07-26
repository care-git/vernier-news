"""add articles.content_type for records that are not one-off stories

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-26

NULL means a normal story article — the overwhelming majority, and the only kind
that gets story-clustered. A non-NULL value marks a record worth keeping that is
not a one-off news story. Only one value exists so far: 'recurring', set when an
outlet republishes an identical headline (the Guardian's daily corrections column,
World Cup fixture listings, NYT live-briefing stubs, BBC radio-programme entries).

These are kept rather than rejected because several are future assets — the
corrections column feeds the correction-record dimension of the feature analysis
system — but clustering them groups months of unrelated instalments under a single
headline and inflates the source counts the free tier is built around.

The (outlet_id, title) index backs the recurrence lookup, which runs once per
ingested article and would otherwise sequentially scan the whole corpus.
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str = "0008"
branch_labels = None
depends_on = None

_INDEX = "ix_articles_outlet_title"


def upgrade() -> None:
    op.add_column("articles", sa.Column("content_type", sa.String(32), nullable=True))
    op.create_index(_INDEX, "articles", ["outlet_id", "title"])


def downgrade() -> None:
    op.drop_index(_INDEX, table_name="articles")
    op.drop_column("articles", "content_type")
