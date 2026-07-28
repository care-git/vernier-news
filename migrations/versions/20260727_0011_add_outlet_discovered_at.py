"""add outlets.discovered_at to distinguish curated sources from discovered ones

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-27

Ingestion used to discard any article whose domain was not already in the seeded
outlet list, which inverted the intended relationship: the corpus should discover its
sources from the articles it collects, not be capped by a hand-curated list. Once
connectors create outlets on discovery the table grows from 31 rows to potentially
tens of thousands, and curated and discovered sources need telling apart.

NULL means seeded by scripts/seed.py with MBFC political-leaning data. A timestamp
means the outlet was created because an article from it arrived, with no leaning data
— that gets computed rather than hand-assigned (docs/political-leaning-design.md).

The distinction is not derivable from political_leaning_source, because that column
will read 'computed' for discovered outlets once leaning calculation lands.
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("outlets", sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("outlets", "discovered_at")
