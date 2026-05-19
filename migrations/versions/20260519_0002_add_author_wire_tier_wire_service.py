"""Add author and wire_tier to articles; wire_service to outlets

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("author", sa.String(255), nullable=True))
    op.add_column("articles", sa.Column("wire_tier", sa.Integer, nullable=True))
    op.add_column(
        "outlets",
        sa.Column("wire_service", sa.Boolean, nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("outlets", "wire_service")
    op.drop_column("articles", "wire_tier")
    op.drop_column("articles", "author")
