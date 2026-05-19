"""widen collection_source to text

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-19
"""
from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: str = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "articles",
        "collection_source",
        existing_type=sa.String(50),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "articles",
        "collection_source",
        existing_type=sa.Text(),
        type_=sa.String(50),
        existing_nullable=True,
    )
