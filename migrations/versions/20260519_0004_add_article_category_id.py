"""Add category_id to articles

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id"), nullable=True),
    )
    op.create_index("ix_articles_category_id", "articles", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_articles_category_id", table_name="articles")
    op.drop_column("articles", "category_id")
