"""Add entity_cache to clusters

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("clusters", sa.Column("entity_cache", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("clusters", "entity_cache")
