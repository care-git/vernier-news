from app.models.settings import Setting
from app.pipeline import tuning


def test_defaults_match_shipped_thresholds():
    t = tuning.PipelineTuning()
    assert t.combined_score_threshold == 0.45
    assert t.dedup_max_distance == 0.01
    assert t.semantic_weight == 0.6
    assert t.entity_weight == 0.4


async def test_refresh_overlays_db_values_and_keeps_defaults(db):
    db.add(Setting(key="combined_score_threshold", value=0.7))
    db.add(Setting(key="not_a_real_setting", value=1.0))  # unknown keys are ignored
    await db.flush()

    t = await tuning.refresh(db)

    assert t.combined_score_threshold == 0.7  # overridden from the DB
    assert t.semantic_weight == 0.6  # missing key keeps its default
