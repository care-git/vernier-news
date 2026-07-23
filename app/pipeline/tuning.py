from __future__ import annotations

from dataclasses import dataclass, fields

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import Setting


@dataclass(frozen=True)
class PipelineTuning:
    """Tunable thresholds for the ingest pipeline.

    Defaults are the values the pipeline shipped with (calibrated for
    all-MiniLM-L6-v2). They are overridden per-key by rows in the ``settings``
    table when present, so calibration needs no code change or redeploy.
    """

    # Clustering
    candidate_max_distance: float = 0.6
    combined_score_threshold: float = 0.45
    semantic_weight: float = 0.6
    entity_weight: float = 0.4
    temporal_window_hours: float = 72.0
    dormancy_hours: float = 48.0

    # Deduplication
    dedup_max_distance: float = 0.01
    dedup_window_hours: float = 72.0

    # Wire propagation tiers
    tier1_similarity: float = 0.88
    tier1_window_hours: float = 6.0
    tier2_similarity_high: float = 0.88
    tier2_similarity_low: float = 0.70
    tier2_window_hours: float = 3.0
    tier3_similarity_high: float = 0.70
    tier3_similarity_low: float = 0.62
    tier3_window_hours: float = 4.0


# Process-local cache, refreshed at the start of each pipeline task run.
_current = PipelineTuning()


def current() -> PipelineTuning:
    """Return the tuning most recently loaded in this worker process."""
    return _current


async def refresh(db: AsyncSession) -> PipelineTuning:
    """Reload tuning from the ``settings`` table, overlaying code defaults.

    Unknown keys are ignored; missing keys keep their code default.
    """
    global _current
    result = await db.execute(select(Setting.key, Setting.value))
    overrides = {row.key: row.value for row in result.all()}
    valid = {f.name for f in fields(PipelineTuning)}
    _current = PipelineTuning(**{k: v for k, v in overrides.items() if k in valid})
    return _current
