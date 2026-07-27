# Design — Data Model and Capture Policy

*Status: approved 27 July 2026. Supersedes the ambiguous use of "cluster" in
`CONCEPT.md` and `PROJECT.md`.*

Settles four things that had been implicit: what the aggregation levels are and what
each is called, that a **Thread** layer exists, when data gets captured relative to
when it gets rendered, and how far down the public-data stack the platform goes.

## Why this document exists

`CONCEPT.md` used "cluster" for two mutually exclusive things: the stored group of
articles covering one event, and the loose visual grouping that would appear in the
Obsidian-style graph view. The second was placeholder language for a concept, never
an entity. The collision cost real work — it left the clusterer with no defined
target, so "is this cluster right?" had no answer.

## The aggregation levels

| Term | What it is | Where it lives |
|---|---|---|
| **Article** | One piece of reporting, from one outlet, at one URL | `articles` |
| **Story** | One event, covered by many outlets | `clusters` table |
| **Thread** | An ongoing chain of stories — bounded in time, causally linked | *to be built* |
| **Topic** | A timeless subject, hierarchical and emergent | `docs/categorisation-design.md` |
| **Neighbourhood** | What visually groups in the graph view | Rendered, never stored |

**"Cluster" is retired from prose.** It survives only as the internal table name for
Story; renaming the table costs a migration and touches everything for no functional
gain, and the ambiguity was always in the documents rather than the code. User-facing
language says "story".

**Neighbourhood is not an entity.** It is what the force-directed layout produces at
render time from edges that already exist. Nothing computes or stores it.

## Thread — the missing layer

Threads are the reason the clusterer looked more broken than it is. `make spotcheck`
found six clusters of 300–564 articles: the Iran war, the 2026 World Cup, the European
heatwave. Those are not stories, and they are not topics either — "nuclear
proliferation" is a topic (timeless, a subject); "the June 2026 Iran–Israel exchange"
is a thread (it starts, develops, ends). They were written into the Story table
because Story was the only container available.

`CONCEPT.md` gropes toward this already — §4 Stage 3 describes "story threads
converging", §7 specifies a narrative evolution timeline — but never made Thread an
entity.

Consequences:

- **Story is tuned tight.** An event-level unit: one thing that happened, covered by
  multiple outlets, over hours to days. This is what the free tier's Representative
  Article Score and "847 sources covering this story" assume, and what the digest card
  renders. A two-month, 564-article Story makes both meaningless.
- **Thread aggregates above it.** A Thread links Stories in temporal and causal order.
  It is the natural home for the narrative evolution timeline and for "following" an
  ongoing situation.
- **Topic stays orthogonal.** A Story sits in one or few Threads and several Topics.
  Threads are chains; Topics are subjects.

Schema, lifecycle (threads spawn, split, merge, go quiet) and the discovery rule are
open — see below. Only the concept is settled.

## Capture now, render later

**The rendering order in `PROJECT.md` stands. The capture order moves forward.**

The platform is built foundation-first as a research tool, with the news app as a
projection of that foundation rather than the other way around. That does not mean
building Phase 5 features now. It means that anything those features will consume
must be *captured* now, because the cost curve is severely asymmetric:

- **Cheap now, expensive later.** Entity mentions are already extracted by spaCy at
  ingest and then discarded into a JSONB blob. Persisting them properly costs one
  table and near-zero marginal compute today; reconstructing them later means
  re-running NER over millions of articles.
- **Impossible later.** Social posts get deleted. Outlets go paywalled or dead. Feeds
  rewrite their own history. Data not captured at the time is not recoverable at any
  price.

The test for any new pipeline stage: *if we do not store this now, can we still get
it in two years?* If no, store it, even with nothing rendering it.

## Retention — mark, never delete

Records are classified, not discarded. A duplicate, a recurring format, a wire copy
and a stub are all evidence about how information propagates, which is precisely what
a provenance query wants. `Article.content_type` (migration 0009) is the mechanism.

This corrects a divergence introduced on 26 July: `persist_article` drops duplicate
URL forms entirely, discarding the second URL and its collection path. `CONCEPT.md` §4
Stage 2 always specified collapsing into "a single record with a list of syndication
destinations" — the list is the part that matters for research and the part currently
being thrown away. A syndication record (URL form, collection source, first seen) per
article restores it.

## How deep the public-data stack goes

The platform aggregates and points to source. It does not build an attributable
archive of what private individuals said.

Deeper layers — social posts, forum questions and answers, other public discussion —
are in scope **as aggregate signals and as pointers to primary sources**: volume,
geographic and temporal spread, amplification timing, framing distribution. "This
story was amplified by 40,000 posts across three platforms, peaking six hours before
mainstream pickup" is high-value provenance data. Storing and re-serving those posts
attributed to named individuals is a different product.

Three reasons this boundary is load-bearing rather than fastidious:

- **Legal.** "Publicly available" is not a lawful basis under GDPR. Aggregating
  individuals' posts into a searchable corpus is the profiling activity the regulation
  governs (`PROJECT.md` risk R7).
- **Mission.** `CONCEPT.md` §16 commits to data minimisation as a product principle.
- **Positioning.** What makes comprehensive-aggregation platforms contested is not
  their analytics but unauditable accumulation of individual data. A platform built to
  counter opaque information authority should not become a transparent version of it.

Institutional accounts — organisations, government bodies, verified journalists
publishing primary-source reporting — remain in scope as full sources per
`CONCEPT.md` §3 Layer 3. This document extends that layer to individual-level content
in aggregate form only; it does not relax the institutional rule.

## What this changes in the phase plan

Nothing is removed. Phase 3's soft launch stops being the pacing goal: the foundation
is finished properly first, and users follow. Front-loaded from later phases, capture
only:

1. **Syndication records** — stop discarding duplicate URL forms (immediate).
2. **Entity mentions** — persist what spaCy already extracts. Shares a code path with
   the clustering entity-overlap fix, so the two land together.
3. **Thread** — schema and discovery, after Story is tuned tight.

## Open

- Thread schema, lifecycle states, and the discovery rule (temporal + causal linkage
  over Story centroids, versus a cut of the topic dendrogram).
- Whether a Story may belong to more than one Thread.
- Where aggregate social signals are stored, and at what granularity, without
  retaining attributable post-level records.
