from __future__ import annotations

from dataclasses import dataclass, fields

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import Setting


@dataclass(frozen=True)
class PipelineTuning:
    """Tunable thresholds for the ingest pipeline.

    Defaults are the values the pipeline shipped with, calibrated for the old
    all-MiniLM-L6-v2 embeddings. **They are stale for bge-m3** and are recalibrated
    as part of the clustering rework (docs/clustering-fix-spec.md) — which is done
    by editing the ``settings`` table, not this file. Rows in that table override
    these per key; missing keys fall back to the values here.
    """

    # Clustering — semantic-primary. An article joins a cluster if its similarity to
    # the cluster's nearest member is >= join_semantic_high, OR is >= join_semantic_mid
    # AND entity overlap is >= join_entity_min. Values calibrated for bge-m3 (audit
    # 25 Jul 2026: random pairs ~0.34, same-story pairs ~0.72).
    candidate_max_distance: float = 0.45  # cosine distance; sim > 0.55 to be a candidate
    join_semantic_high: float = 0.78  # semantic-only join
    join_semantic_mid: float = 0.68  # join in this band only with entity corroboration
    join_entity_min: float = 0.30  # entity overlap coefficient required in the mid band
    temporal_window_hours: float = 72.0
    dormancy_hours: float = 48.0

    # Deduplication
    dedup_max_distance: float = 0.01
    dedup_window_hours: float = 72.0

    # Wire propagation tiers. Raised for bge-m3: wire copy is near-identical text
    # (~0.95+), so the old MiniLM bands (0.70–0.88) mislabelled independent same-story
    # reporting as wire. Conservative — under-detects rather than over-collapses;
    # proper calibration against labelled wire pairs is a Phase 3 task.
    tier1_similarity: float = 0.95
    tier1_window_hours: float = 6.0
    tier2_similarity_high: float = 0.95
    tier2_similarity_low: float = 0.90
    tier2_window_hours: float = 3.0
    tier3_similarity_high: float = 0.90
    tier3_similarity_low: float = 0.86
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
