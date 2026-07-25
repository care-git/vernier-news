from app.models.settings import Setting
from app.pipeline import tuning


def test_defaults_match_shipped_thresholds():
    t = tuning.PipelineTuning()
    assert t.join_semantic_high == 0.78
    assert t.join_semantic_mid == 0.68
    assert t.join_entity_min == 0.30
    assert t.dedup_max_distance == 0.01


async def test_refresh_overlays_db_values_and_keeps_defaults(db):
    db.add(Setting(key="join_semantic_high", value=0.85))
    db.add(Setting(key="not_a_real_setting", value=1.0))  # unknown keys are ignored
    await db.flush()

    t = await tuning.refresh(db)

    assert t.join_semantic_high == 0.85  # overridden from the DB
    assert t.join_semantic_mid == 0.68  # missing key keeps its default
