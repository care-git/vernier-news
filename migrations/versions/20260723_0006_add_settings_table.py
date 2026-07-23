"""add settings table for pipeline tuning

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-23
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str = "0005"
branch_labels = None
depends_on = None

# Seed values match the code defaults in app/pipeline/tuning.py (calibrated for
# all-MiniLM-L6-v2). They will be recalibrated after the bge-m3 embedding upgrade.
_DEFAULTS = [
    ("candidate_max_distance", 0.6, "clustering", "Max cosine distance for a cluster candidate"),
    ("combined_score_threshold", 0.45, "clustering", "Min combined score to join a cluster"),
    ("semantic_weight", 0.6, "clustering", "Weight of semantic similarity in the combined score"),
    ("entity_weight", 0.4, "clustering", "Weight of entity overlap in the combined score"),
    ("temporal_window_hours", 72.0, "clustering", "Lookback window for cluster candidates"),
    ("dormancy_hours", 48.0, "clustering", "Idle hours before a cluster is marked dormant"),
    ("dedup_max_distance", 0.01, "dedup", "Max cosine distance treated as a near-duplicate"),
    ("dedup_window_hours", 72.0, "dedup", "Lookback window for near-duplicate detection"),
    ("tier1_similarity", 0.88, "wire", "Tier 1 high-confidence wire similarity"),
    ("tier1_window_hours", 6.0, "wire", "Tier 1 lookback window (hours)"),
    ("tier2_similarity_high", 0.88, "wire", "Tier 2 upper similarity bound"),
    ("tier2_similarity_low", 0.70, "wire", "Tier 2 lower similarity bound"),
    ("tier2_window_hours", 3.0, "wire", "Tier 2 lookback window (hours)"),
    ("tier3_similarity_high", 0.70, "wire", "Tier 3 upper similarity bound"),
    ("tier3_similarity_low", 0.62, "wire", "Tier 3 lower similarity bound"),
    ("tier3_window_hours", 4.0, "wire", "Tier 3 lookback window (hours)"),
]


def upgrade() -> None:
    settings = op.create_table(
        "settings",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("category", sa.String(32), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.bulk_insert(
        settings,
        [{"key": k, "value": v, "category": c, "description": d} for (k, v, c, d) in _DEFAULTS],
    )


def downgrade() -> None:
    op.drop_table("settings")
