"""recalibrate clustering + wire thresholds for bge-m3

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-25

Replaces the weighted-combined clustering model (semantic_weight / entity_weight /
combined_score_threshold) with the semantic-primary model (join_semantic_high /
join_semantic_mid / join_entity_min), and lifts the wire-tier bands into bge-m3's
scale. Values match the code defaults in app/pipeline/tuning.py. All are editable
rows afterwards — calibration is a data change, not a redeploy.
"""

from alembic import op

revision: str = "0008"
down_revision: str = "0007"
branch_labels = None
depends_on = None

# Obsolete keys from the MiniLM-era weighted-combined model.
_DROP = ("combined_score_threshold", "semantic_weight", "entity_weight")

# key -> (value, category, description)
_UPSERT = {
    "candidate_max_distance": (0.45, "clustering", "Max cosine distance for a cluster candidate"),
    "join_semantic_high": (0.78, "clustering", "Similarity for a semantic-only cluster join"),
    "join_semantic_mid": (0.68, "clustering", "Similarity floor for an entity-corroborated join"),
    "join_entity_min": (0.30, "clustering", "Entity overlap coefficient required in the mid band"),
    "tier1_similarity": (0.95, "wire", "Tier 1 high-confidence wire similarity"),
    "tier2_similarity_high": (0.95, "wire", "Tier 2 upper similarity bound"),
    "tier2_similarity_low": (0.90, "wire", "Tier 2 lower similarity bound"),
    "tier3_similarity_high": (0.90, "wire", "Tier 3 upper similarity bound"),
    "tier3_similarity_low": (0.86, "wire", "Tier 3 lower similarity bound"),
}


def upgrade() -> None:
    for key in _DROP:
        op.execute(f"DELETE FROM settings WHERE key = '{key}'")
    for key, (value, category, description) in _UPSERT.items():
        op.execute(
            "INSERT INTO settings (key, value, category, description) "
            f"VALUES ('{key}', {value}, '{category}', '{description}') "
            f"ON CONFLICT (key) DO UPDATE SET value = {value}, description = '{description}'"
        )


def downgrade() -> None:
    # Restore the MiniLM-era clustering keys; wire values revert to their 0006 seeds.
    for key in ("join_semantic_high", "join_semantic_mid", "join_entity_min"):
        op.execute(f"DELETE FROM settings WHERE key = '{key}'")
    op.execute(
        "INSERT INTO settings (key, value, category, description) VALUES "
        "('combined_score_threshold', 0.45, 'clustering', 'Min combined score to join a cluster'),"
        "('semantic_weight', 0.6, 'clustering', 'Weight of semantic similarity in the combined score'),"
        "('entity_weight', 0.4, 'clustering', 'Weight of entity overlap in the combined score') "
        "ON CONFLICT (key) DO NOTHING"
    )
    for key, value in (
        ("candidate_max_distance", 0.6),
        ("tier1_similarity", 0.88),
        ("tier2_similarity_high", 0.88),
        ("tier2_similarity_low", 0.70),
        ("tier3_similarity_high", 0.70),
        ("tier3_similarity_low", 0.62),
    ):
        op.execute(f"UPDATE settings SET value = {value} WHERE key = '{key}'")
