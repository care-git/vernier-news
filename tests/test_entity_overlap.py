from app.pipeline.clustering import Mention, _entity_overlap, entities_from_mentions
from app.pipeline.tuning import PipelineTuning


def _corroborated(article: list[str], cluster: list[str], t: PipelineTuning) -> bool:
    """The mid-band entity clause exactly as assign_cluster applies it."""
    overlap, shared = _entity_overlap(article, cluster)
    return shared >= t.join_entity_min_shared and overlap >= t.join_entity_min


def test_one_shared_entity_no_longer_corroborates_a_join():
    """The attractor bug: a 3-entity article scored 1/3 = 0.33 against a huge cluster."""
    t = PipelineTuning()
    article = ["Trump", "Iran", "Hormuz"]
    cluster = ["Trump"] + [f"Entity {n}" for n in range(500)]

    overlap, shared = _entity_overlap(article, cluster)

    assert shared == 1
    assert overlap >= t.join_entity_min  # the coefficient alone still passes
    assert not _corroborated(article, cluster, t)  # the count is what stops it


def test_two_shared_entities_still_corroborate():
    """The fix must only remove single-entity joins, not genuine corroboration."""
    t = PipelineTuning()
    article = ["Trump", "Iran", "Hormuz"]
    cluster = ["Trump", "Iran", "Strait of Hormuz"]

    assert _corroborated(article, cluster, t)


def test_a_large_entity_cache_cannot_manufacture_corroboration():
    """A cluster accumulating every entity it ever saw must not become an attractor."""
    t = PipelineTuning()
    article = ["Manuel Neuer", "Germany", "Bayern Munich", "Julian Nagelsmann"]
    # A months-old cluster whose cache happens to contain "Germany".
    cluster = ["Germany"] + [f"Entity {n}" for n in range(2000)]

    assert not _corroborated(article, cluster, t)


def test_overlap_reports_both_ratio_and_count():
    overlap, shared = _entity_overlap(["a1", "b1", "c1"], ["a1", "b1"])

    assert shared == 2
    assert overlap == 1.0  # divided by the smaller set, which is the cluster's here


def test_titles_are_stripped_before_comparison():
    """'President Trump' and 'Trump' are the same entity for overlap purposes."""
    _, shared = _entity_overlap(["President Trump", "Iran"], ["Trump", "Iran"])

    assert shared == 2


def test_empty_entity_lists_never_corroborate():
    assert _entity_overlap([], ["Trump"]) == (0.0, 0)
    assert _entity_overlap(["Trump"], []) == (0.0, 0)


def test_entities_from_mentions_deduplicates_but_keeps_order():
    mentions = [
        Mention("Trump", "trump", "PERSON", 0),
        Mention("Iran", "iran", "GPE", 10),
        Mention("Trump", "trump", "PERSON", 40),
    ]

    assert entities_from_mentions(mentions) == ["Trump", "Iran"]
