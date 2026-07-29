from app.pipeline.ingestion.sources import (
    SOURCE_TYPE_ACADEMIC,
    SOURCE_TYPE_AGGREGATOR,
    SOURCE_TYPE_FORUM,
    SOURCE_TYPE_GOVERNMENT,
    SOURCE_TYPE_PRESS_RELEASE,
    SOURCE_TYPE_SATIRE,
    classify_source,
    registrable_domain,
)


def test_subdomains_group_under_their_registrable_domain():
    """Discovery created these as separate outlets; they need grouping, not merging."""
    assert registrable_domain("timesofindia.indiatimes.com") == "indiatimes.com"
    assert registrable_domain("indiatimes.com") == "indiatimes.com"
    assert registrable_domain("wmmbam.iheart.com") == "iheart.com"
    assert registrable_domain("kfbk.iheart.com") == "iheart.com"


def test_multi_part_suffixes_are_not_split_on_dots():
    """The whole reason for a public suffix list: bbc.co.uk must not become co.uk."""
    assert registrable_domain("bbc.co.uk") == "bbc.co.uk"
    assert registrable_domain("news.bbc.co.uk") == "bbc.co.uk"
    assert registrable_domain("na.gov.pk") == "na.gov.pk"


def test_registrable_domain_is_not_ownership():
    """Same company, different registrable domains — ownership is the influence graph."""
    assert registrable_domain("aol.com") != registrable_domain("aol.co.uk")


def test_government_is_recognised_from_the_public_suffix():
    """Suffix beats string matching: 'gov' appears in plenty of ordinary domains."""
    assert classify_source("na.gov.pk") == SOURCE_TYPE_GOVERNMENT
    assert classify_source("www.gov.uk") == SOURCE_TYPE_GOVERNMENT
    assert classify_source("whitehouse.gov") == SOURCE_TYPE_GOVERNMENT


def test_academic_suffixes_and_publishers_are_recognised():
    assert classify_source("mit.edu") == SOURCE_TYPE_ACADEMIC
    assert classify_source("ox.ac.uk") == SOURCE_TYPE_ACADEMIC
    assert classify_source("link.springer.com") == SOURCE_TYPE_ACADEMIC


def test_seeded_publisher_kinds_are_recognised_through_subdomains():
    assert classify_source("prnewswire.com") == SOURCE_TYPE_PRESS_RELEASE
    assert classify_source("thedailymash.co.uk") == SOURCE_TYPE_SATIRE
    assert classify_source("reddit.com") == SOURCE_TYPE_FORUM
    assert classify_source("finance.yahoo.com") == SOURCE_TYPE_AGGREGATOR


def test_ordinary_journalism_is_left_unclassified():
    """Domain shape cannot recognise journalism, so it must not pretend to."""
    assert classify_source("theguardian.com") is None
    assert classify_source("bbc.co.uk") is None
    assert classify_source("some-local-paper.example") is None


def test_empty_domain_classifies_to_nothing():
    assert classify_source("") is None
    assert registrable_domain("") is None
