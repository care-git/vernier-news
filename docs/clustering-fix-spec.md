# Spec — Clustering Fix

*Status: draft for review*

Clustering is over-fragmenting: **21,329 active clusters from 35,931 articles (~1.7
articles/cluster)** — mostly singletons. This defeats the platform's core value unit
(multiple independent perspectives grouped per story) and makes precompute
needlessly heavy. This spec fixes it. It must land **before** categorisation, which
is built on top of clusters.

## Diagnosis (from the current code)

The join rule in `app/pipeline/clustering.py` (`assign_cluster`):

```
combined = 0.6 * semantic_similarity + 0.4 * entity_jaccard
join the cluster if combined >= 0.45, else seed a new one
```

Root causes of fragmentation:

1. **Entity Jaccard is brittle and systematically low.** It is exact, lowercased
   string-set overlap of `en_core_web_sm` entities. "Trump" / "Donald Trump" /
   "President Trump" don't match; "US" / "United States" don't; non-English articles
   yield almost no entities from the English model. Typical overlap for genuinely
   related articles is ~0.1–0.2 — and at weight 0.4 it *drags the score down*.
   - Worked example: semantic 0.60, Jaccard 0.20 → `0.6·0.60 + 0.4·0.20 = 0.44` →
     **below 0.45 → new singleton.**
2. **MiniLM semantic similarity is moderate and English-centric.** Same-event,
   cross-outlet similarity is often only ~0.5–0.7; cross-language much lower. The
   candidate gate (`cosine_distance < 0.6`, i.e. similarity > 0.4) can exclude
   related pairs outright.
3. **Thresholds are hardcoded constants** (`_COMBINED_SCORE_THRESHOLD` etc.) — the
   code comments say "moved to DB settings table in Phase 3," but that never
   happened, so calibration requires a code change + redeploy.
4. **Greedy, order-dependent assignment.** Each article is matched once, at ingest,
   to the best existing cluster; there is no pass that corrects earlier mis-splits.

## Fixes

### 1. Embedding upgrade — bge-m3 (shared foundation)

The embedding model is the shared substrate for dedup, clustering, and (soon)
categorisation, so this upgrade is foundational and is the first consumer's
responsibility to land here.

- **Model:** `BAAI/bge-m3` — multilingual, 1024-dim, 8k context, strong same-event
  separation. Multilingual is the mission-critical gain: it lets a French, Arabic,
  and English article on the same event cluster together.
- **Footprint:** run **quantized (ONNX int8)** → ~1.5–2 GB resident in the worker
  (vs ~2.5–3.5 GB fp32), comfortably within the ~5 GB free on the 8 GB VPS. No
  query/passage prefix required (unlike e5), so it's operationally simpler.
- **Schema:** `Article.embedding` `Vector(384)` → `Vector(1024)`; Alembic migration;
  HNSW index rebuild.
- **Backfill:** re-embed the existing corpus (batch job; hours, not days).
- **Re-tune:** dedup (`< 0.01`) and clustering thresholds are calibrated to MiniLM's
  distance distribution and **must be recalibrated** to bge-m3's (see §5).

### 2. Rescore — semantic-primary, entity as a booster (not a gate)

- Make semantic similarity the primary signal; entity overlap **adds** confidence
  but never suppresses a strong semantic match.
- Proposed rule (final form set by calibration in §5):
  ```
  join if  semantic >= T_high
        or (semantic >= T_mid and entity_overlap >= E_min)
  ```
  With bge-m3's tighter same-event similarity, a semantic-only `T_high` (~0.78–0.85,
  to calibrate) will capture most true matches; the entity clause rescues mid-similarity
  pairs that share strong entities.

### 3. De-brittle the entity signal

- Normalise entities: lowercase, strip honorifics/titles, collapse whitespace.
- Replace exact-set Jaccard with an **overlap coefficient** (`|A∩B| / min(|A|,|B|)`),
  which isn't punished by union size, and allow token-level/containment matches
  ("Trump" ⊂ "Donald Trump").
- Full Wikidata entity linking stays Phase 4; this is the cheap interim win.

### 4. Language-aware handling

- Never penalise a non-English article for empty English NER: when entities are
  sparse/absent, fall back to the semantic-only branch. bge-m3 makes this reliable.
- (Optional) multilingual NER later; not required once embeddings carry clustering.

### 5. Calibratable thresholds — `settings` table

- Create a typed key/value `settings` table (Alembic migration). Move clustering,
  dedup, and wire-tier thresholds into it; load at task start with sane defaults.
- Enables empirical calibration against the live corpus without code changes — the
  long-stated PROJECT intent. Calibrate `T_high`, `T_mid`, `E_min`, candidate gate,
  and the dedup threshold against a labelled sample after the embedding swap.

### 6. Consolidation pass (fix existing fragmentation + ongoing correction)

- Periodic Celery Beat batch job: within the temporal window, find active clusters
  whose **centroids** are within `merge_distance` and **merge** them (combine
  memberships + entity caches, recompute metadata, record lineage). This directly
  attacks the existing 21k singletons and corrects greedy order-dependence going
  forward.

### 7. Backfill

- Re-embed all articles with bge-m3, then re-cluster: run the consolidation pass
  across the corpus (recommend actively re-clustering the last ~30–60 days; older
  content can consolidate in place or be archived). Target a sane ratio — for real
  news corpora, expect meaningfully more than 1.7 articles/cluster on active stories.

## Sequencing

1. `settings` table + migrate thresholds out of code.
2. Embedding upgrade (bge-m3, quantized ONNX) + `Vector(1024)` migration + corpus
   re-embed + HNSW rebuild.
3. Rescore + entity normalisation + language-aware fallback.
4. Calibrate thresholds on the real corpus (labelled spot-check sample).
5. Consolidation pass + backfill re-cluster.
6. Verify the cluster/article ratio and eyeball a sample of merged clusters.

## RAM & ops

- bge-m3 (int8) resident in the worker ~1.5–2 GB; cap Postgres `shared_buffers`/
  `work_mem` to keep headroom; run heavy batch jobs (re-embed, re-cluster) off-peak.
- Consider running the re-embed/consolidation as an **ephemeral** process (load →
  compute → exit) rather than resident, to bound peak memory.

## Risks

- **Over-merging** (distinct stories collapsed) if thresholds go too loose —
  mitigate with calibration, keep thresholds in `settings`, and always surface the
  underlying member list so mistakes are visible and reportable.
- Re-embedding/backfill compute cost — one-off, hours, run off-peak.
