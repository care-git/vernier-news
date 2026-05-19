"""Initial MVP schema

Revision ID: 0001
Revises:
Create Date: 2026-05-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "outlets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False, unique=True),
        sa.Column("country", sa.String(2)),
        sa.Column("language_primary", sa.String(10)),
        sa.Column("political_leaning_lr", sa.Float),
        sa.Column("political_leaning_source", sa.String(100)),
        sa.Column("parent_org_name", sa.String(255)),
        sa.Column("rss_feed_url", sa.Text),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
    )

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("url", sa.Text, nullable=False, unique=True),
        sa.Column("outlet_id", sa.Integer, sa.ForeignKey("outlets.id"), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("summary", sa.Text),
        sa.Column("body", sa.Text),
        sa.Column("language", sa.String(10)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column(
            "collected_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("collection_source", sa.String(50)),
        sa.Column("wire_flag", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("embedding", Vector(384)),
    )
    op.create_index("ix_articles_outlet_id", "articles", ["outlet_id"])
    op.create_index("ix_articles_published_at", "articles", ["published_at"])

    op.create_table(
        "clusters",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("first_published_at", sa.DateTime(timezone=True)),
        sa.Column(
            "last_updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id")),
        sa.Column("total_source_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("independent_source_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    )
    op.create_index("ix_clusters_active", "clusters", ["active"])

    op.create_table(
        "article_cluster",
        sa.Column("article_id", sa.Integer, sa.ForeignKey("articles.id"), primary_key=True),
        sa.Column("cluster_id", sa.Integer, sa.ForeignKey("clusters.id"), primary_key=True),
        sa.Column("independence_score", sa.Float, nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "tier",
            sa.Enum("free", "professional", "academic", "enterprise", name="usertier"),
            nullable=False,
            server_default="free",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("last_login", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("categories", sa.dialects.postgresql.JSONB),
        sa.Column("depth_preference", sa.String(20)),
        sa.Column("digest_time", sa.Time(timezone=True)),
        sa.Column("notification_settings", sa.dialects.postgresql.JSONB),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS usertier")
    op.drop_table("article_cluster")
    op.drop_table("clusters")
    op.drop_table("articles")
    op.drop_table("categories")
    op.drop_table("outlets")
    op.execute("DROP EXTENSION IF EXISTS vector")
