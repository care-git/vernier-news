"""Derive grouping and kind for a source domain.

Two independent pieces of outlet metadata, both computed from the domain alone:

**Registrable domain** groups sibling sites. Ingestion discovers subdomains as
separate outlets — timesofindia.indiatimes.com alongside indiatimes.com, three iHeart
stations under iheart.com — and that separation is correct, because those genuinely
are different publications. But they need grouping, which cannot be done by splitting
on dots: bbc.co.uk would reduce to co.uk. The public suffix list handles it.

This is **not ownership**. aol.co.uk and aol.com are different registrable domains and
the same company. Documented ownership is the influence graph (CONCEPT.md §7, Phase
4); this is a mechanical grouping and must not be presented as more than that.

**Source type** records what kind of publisher a domain is. Per "filter nothing,
classify everything" (docs/data-model.md) nothing is excluded on this basis — a
satirical piece is a real part of the information landscape and worth mapping. But it
has to be identifiable, so users can filter graph views and so counting can treat it
correctly: satire and press releases are coverage (`total_source_count`) but not
corroboration (`independent_source_count`).

Most outlets stay NULL. The rules below are a documented seed, not a taxonomy claim —
domain shape can only ever recognise the unambiguous cases, and journalism itself is
not detectable this way.
"""

from __future__ import annotations

import tldextract

# suffix_list_urls=() pins the bundled snapshot: no network fetch at ingest time, and
# the same answer in every environment. Refreshed by upgrading the package.
_extract = tldextract.TLDExtract(suffix_list_urls=())

SOURCE_TYPE_PRESS_RELEASE = "press_release"
SOURCE_TYPE_ACADEMIC = "academic"
SOURCE_TYPE_GOVERNMENT = "government"
SOURCE_TYPE_NGO = "ngo"
SOURCE_TYPE_SATIRE = "satire"
SOURCE_TYPE_FORUM = "forum"
SOURCE_TYPE_AGGREGATOR = "aggregator"
# Journalism cannot be recognised from a domain, so nothing is auto-classified as
# news. It is set for the curated seed list and by later review.
SOURCE_TYPE_NEWS = "news"

# Public suffixes that identify a publisher outright, checked before any name list.
_GOVERNMENT_SUFFIXES = ("gov", "mil", "gouv")
_ACADEMIC_SUFFIXES = ("edu", "ac")

# Seed lists. Deliberately short: every entry is a judgement, so they are kept
# reviewable rather than exhaustive, and extended from what ingestion actually finds.
_BY_REGISTRABLE_DOMAIN = {
    "prnewswire.com": SOURCE_TYPE_PRESS_RELEASE,
    "globenewswire.com": SOURCE_TYPE_PRESS_RELEASE,
    "businesswire.com": SOURCE_TYPE_PRESS_RELEASE,
    "epnewswire.com": SOURCE_TYPE_PRESS_RELEASE,
    "einpresswire.com": SOURCE_TYPE_PRESS_RELEASE,
    "prweb.com": SOURCE_TYPE_PRESS_RELEASE,
    "newswire.ca": SOURCE_TYPE_PRESS_RELEASE,
    "springer.com": SOURCE_TYPE_ACADEMIC,
    "frontiersin.org": SOURCE_TYPE_ACADEMIC,
    "arxiv.org": SOURCE_TYPE_ACADEMIC,
    "biorxiv.org": SOURCE_TYPE_ACADEMIC,
    "ssrn.com": SOURCE_TYPE_ACADEMIC,
    "plos.org": SOURCE_TYPE_ACADEMIC,
    "reddit.com": SOURCE_TYPE_FORUM,
    "ycombinator.com": SOURCE_TYPE_FORUM,
    "dev.to": SOURCE_TYPE_FORUM,
    "quora.com": SOURCE_TYPE_FORUM,
    "stackexchange.com": SOURCE_TYPE_FORUM,
    "thedailymash.co.uk": SOURCE_TYPE_SATIRE,
    "theonion.com": SOURCE_TYPE_SATIRE,
    "newsthump.com": SOURCE_TYPE_SATIRE,
    "thebeaverton.com": SOURCE_TYPE_SATIRE,
    "waterfordwhispersnews.com": SOURCE_TYPE_SATIRE,
    "babylonbee.com": SOURCE_TYPE_SATIRE,
    "yahoo.com": SOURCE_TYPE_AGGREGATOR,
    "msn.com": SOURCE_TYPE_AGGREGATOR,
    "aol.com": SOURCE_TYPE_AGGREGATOR,
    "aol.co.uk": SOURCE_TYPE_AGGREGATOR,
    "flipboard.com": SOURCE_TYPE_AGGREGATOR,
}


def registrable_domain(domain: str) -> str | None:
    """Return the domain one level under its public suffix, for grouping siblings."""
    if not domain:
        return None
    return _extract(domain).top_domain_under_public_suffix or None


def classify_source(domain: str) -> str | None:
    """Return a source type for a domain, or None when its kind is not evident.

    None is the expected answer for most outlets and means unclassified, never
    "excluded" — nothing is dropped on the basis of this value.
    """
    if not domain:
        return None

    parts = _extract(domain)
    suffix_labels = set(parts.suffix.split(".")) if parts.suffix else set()
    if suffix_labels & set(_GOVERNMENT_SUFFIXES):
        return SOURCE_TYPE_GOVERNMENT
    if suffix_labels & set(_ACADEMIC_SUFFIXES):
        return SOURCE_TYPE_ACADEMIC

    return _BY_REGISTRABLE_DOMAIN.get(parts.top_domain_under_public_suffix or "")
