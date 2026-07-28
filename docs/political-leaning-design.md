# Design — Political Leaning, Computed

*Status: conceptual design for review, 27 July 2026.*

Replaces hardcoded MBFC scores with leaning the platform calculates for itself, at
both outlet and author level, across the three axes `CONCEPT.md` §6 specifies. MBFC
becomes the calibration reference and cold-start fallback rather than the input.

This is forced rather than optional: once ingestion creates outlets on discovery
(`docs/data-model.md`), the outlets table grows from 31 to potentially tens of
thousands, and hand-maintained per-outlet scores stop being possible.

## The confound that shapes the method

Embedding an outlet's articles and looking for structure mostly learns **what it
covers**, not how it covers it. An outlet writing heavily on immigration separates
from one writing on climate regardless of political position. That is topic
selection, not framing.

The control is to **compare within a story**. Inside one Story every outlet is
describing the same event, so differences between them are framing differences with
topic held constant. `CONCEPT.md` §6 already names this signal — "how does this
outlet's coverage of the same event compare to the distributional average of all
coverage?"

    article framing signature = article embedding − centroid of its Story

Aggregating an outlet's signatures across many stories gives its systematic tilt.

**This makes the method dependent on clustering quality.** With 84.6% of clusters
singleton, the usable sample is small; tightening Story to event level is a
prerequisite, not a parallel track.

## Three named axes, not discovered components

`CONCEPT.md` §6 requires named axes — economic (interventionist ↔ laissez-faire),
social (progressive ↔ conservative), institutional (establishment ↔
anti-establishment) — with left/right as an explicitly labelled surface
simplification and per-region contextualisation.

Unsupervised decomposition cannot deliver those. PCA returns unnamed orthogonal
components ordered by variance; mapping them onto three political concepts after the
fact is editorial judgement wearing the costume of objectivity.

Instead each axis is defined by **contrastive probe pairs**: short texts expressing
each pole's framing of the same question. The axis is the normalised difference
between the two pole means, and an outlet's position is the projection of its framing
signature onto it.

    axis = normalise( mean(embeddings of pole A) − mean(embeddings of pole B) )
    position = framing signature · axis

Why this fits the project:

- Axes are **named by construction**, not by post-hoc interpretation.
- The editorial input reduces to a **probe set** — small, enumerable, and publishable
  in full, which is what §6's "methodology transparency is non-negotiable" demands.
- It is **challengeable through the RFC process** (§15) in a way a hardcoded score
  never is.
- It is **testable**: a probe set that fails to separate outlets in ways that
  correlate with independent data is a bad probe set, and that can be demonstrated.

## PCA's two roles

**Diagnostic.** How much of the observed framing variation do the three named axes
actually explain? If the dominant component correlates with none of them, the axes
are missing the real structure — a publishable finding rather than a failure.

**The surface left/right indicator.** §6 keeps left/right as the entry point for
casual users, and the empirically dominant axis is a defensible basis for it. But a
continuously recomputed PC1 **rotates as the corpus grows**, so a displayed score
would drift for reasons unrelated to anything an outlet published.

The axis is therefore **frozen and versioned**: fit once on a reference corpus, store
the vector, project everything onto it, and refit only deliberately with a public
changelog entry per §15. Empirical derivation and stability at once.

## Outlet and author together

An article's framing is an outlet effect plus an author effect plus story-specific
noise. Estimating both in one mixed-effects model beats computing them separately: it
handles journalists moving between employers, which §5 requires ("a journalist's
history does not reset when they change employer"), and yields confidence intervals,
so a thinly-published author reports as uncertain rather than as a number.

**What the corpus supports** (27 July 2026, 38.7k articles):

| threshold | authors | articles |
|---|---|---|
| ≥50 | 24 | 4,408 |
| ≥20 | 178 | 8,621 |
| ≥10 | 508 | 13,010 |
| ≥5 | 1,031 | 16,434 |
| 1–4 only | 6,845 | 9,340 |

Byline presence is near all-or-nothing per outlet: Guardian 97%, NYT 95%, France 24
97%, Independent 95%, El País 100%, Vice 100% — against Al Jazeera 0%, Economist 0%,
Der Spiegel 0%, DW 1%, BBC 3%, AP 4%. The field is simply null for the second group,
not boilerplate.

**Two consequences that must be reported, not absorbed:**

- Author-level estimates are computable almost exclusively for **left-of-centre
  outlets**, since those are the ones publishing bylines. This is a worse sampling
  problem than the outlet level has.
- 87% of distinct author strings have 1–4 articles, partly a real long tail and partly
  co-bylines creating phantom authors. Byline splitting and normalisation precede any
  thresholding.

§6 wants three indicators per article: publishing outlet, current author, and the
original article's author where the piece is a reprint. The third needs provenance
chains (Phase 5); the first two are buildable now, and the gap is stated rather than
quietly dropped.

## The origin is the corpus, and that must be published

Measuring deviation from a Story centroid means zero is **the consensus framing of
that story within our corpus**, not a neutral point in the world. With the corpus at
53% centre-left, "neutral" is centre-left. This cannot be engineered away and must not
be hidden. It is a further reason the aggregation inversion matters: a broader corpus
moves the origin somewhere more defensible.

It also argues for a better output than one number. Report **both** the story's
consensus position on each axis **and** each outlet's deviation from it, so a
researcher sees "coverage of this event clustered here; these outlets diverged in this
direction". More informative and more honest than an absolute score.

That single computation serves three separate features: political leaning (§6),
framing divergence (§9), and the RAS political-centroid dimension (§11).

## Regional contextualisation

§6 requires per-region calibration — "establishment" in Hungary is not "establishment"
in the UK. With probe axes this is natural: **axis names stay fixed, probe sets vary
by region**. Because bge-m3 is multilingual, probes can be written in the region's own
language and still land in the same vector space — a payoff from the embedding choice
that was not part of its original justification.

## Validation

MBFC is the check, not the input. Computing an axis independently and then
demonstrating correlation against an independent public dataset is a far stronger
methodological claim than adopting that dataset's numbers, and it is auditable, which
is the platform's whole differentiator. MBFC values are retained as cold-start
fallback and calibration reference exactly as `PROJECT.md` Phase 4 specifies.

## Known limitations

- **bge-m3 is trained for semantic similarity, not stylistic separation.** Framing
  deviations may partly capture which aspect of an event a piece emphasises rather
  than its political framing. Domain fine-tuning is the eventual fix.
- **Body length matters here, unlike clustering.** Framing lives in prose, and roughly
  half the corpus is RSS summaries. This is an independent justification for Layer 4
  full-text enrichment, distinct from the clustering rationale that was falsified.
- **GDELT-sourced articles carry no body at all**, so breadth from GDELT improves
  clustering and coverage distribution but contributes nothing here. Leaning analysis
  stays dependent on the full-text outlets.

## Sequencing

1. Tighten Story to event level (prerequisite — the within-story control needs
   multi-outlet stories).
2. Byline splitting and author normalisation.
3. Draft and publish probe sets per axis; validate separation against MBFC.
4. Outlet-level positions on three axes, plus the frozen surface axis.
5. Author-level via mixed effects, with confidence intervals and the sampling caveat
   surfaced in the UI.
6. Per-region probe sets.

## Open

- Probe set content — the one part needing editorial judgement, and the part most
  likely to be challenged. Draft publicly from the start.
- Minimum article threshold per author (≥10 gives 508 authors; ≥20 gives 178).
- Whether the surface axis is a frozen PC1 or a probe-defined left/right axis. PC1 is
  empirically grounded; a probe axis is stable by construction and consistent with the
  other three. Decide after seeing whether they correlate.
