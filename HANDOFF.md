# Vernier News — Handoff Document

*Last updated: May 2026*

---

## What this project is

Vernier News is a global media intelligence platform. Not a news aggregator — an analytical layer that maps who covers stories, from what political position, with what ownership relationships, and with what coverage distribution across the world. The name comes from the vernier scale: the precision mechanism that measures what blunt instruments miss.

Full concept: `CONCEPT.md`. Full build plan: `PROJECT.md`. Both are v0.4, approved for development.

---

## Current state

### Phase 0 — complete and deployed

Phase 0 is fully running on the VPS. Health check passes, all migrations are applied, seed data loaded.

**Working directory:** `/Users/billy/Projects/vernier/`

```
app/
  main.py               — FastAPI app, all routers registered, CORS, /health endpoint
  config.py             — pydantic-settings, extra="ignore" for POSTGRES_* vars
  database.py           — async SQLAlchemy engine, Base, get_db dependency
  worker.py             — Celery app (celery_app), Beat schedule, autodiscover pipeline tasks
  redis_client.py       — aioredis client singleton
  auth/
    router.py           — POST /api/v1/auth/register, /login, /refresh
    utils.py            — Argon2 password hashing, JWT create/decode
    dependencies.py     — get_current_user FastAPI dependency
    schemas.py          — RegisterRequest, LoginRequest, TokenResponse
  models/
    article.py          — Article (pgvector embedding, wire_tier, category_id, author)
    outlet.py           — Outlet (political_leaning_lr float, wire_service bool)
    cluster.py          — Cluster (entity_cache JSONB) + ArticleCluster join table
    category.py         — Category (name, slug)
    user.py             — User (UserTier enum) + UserPreferences (JSONB)
  routers/
    articles.py         — GET /articles/, GET /articles/{id} (auth required)
    clusters.py         — GET /clusters/, GET /clusters/{id} (auth required)
    outlets.py          — GET /outlets/, GET /outlets/{id} (public)
    users.py            — GET /users/me (auth required)
    digest.py           — GET /digest/ stub (Phase 2 deliverable)
  pipeline/
    tasks.py            — 5 Celery tasks: ingest_feeds, cluster_pass, categorise_pending,
                          precompute_cluster_summaries_task, precompute_digests
    dedup.py            — sentence-transformers embed, URL+cosine dedup, wire tier detection
    clustering.py       — spaCy NER, pgvector candidate search, Jaccard+cosine scoring
    categorise.py       — Ollama (Mistral 7B) categorisation, graceful failure if unavailable
    ingestion/
      normalise.py      — NormalisedArticle dataclass, HTML strip (bs4/lxml), langdetect
      rss.py            — parse_opml(), ingest_feed(), ingest_opml()
      connectors/
        guardian.py     — Guardian Content API (full bodyText)
        gnews.py        — GNews top-headlines
        currents.py     — Currents latest-news
        nyt.py          — NYT Top Stories API (7 sections)
        gdelt.py        — GDELT doc API (no key required)
        hackernews.py   — HN Firebase API, top 30 stories (no key required)
  cache/
    clusters.py         — precompute_cluster_summaries(), get_cluster_summary()
    digest.py           — precompute_all_digests(), get_digest()
migrations/
  versions/
    20260517_0001_initial_schema.py         — full MVP schema, pgvector extension
    20260519_0002_add_author_wire_tier_wire_service.py
    20260519_0003_add_cluster_entity_cache.py
    20260519_0004_add_article_category_id.py
scripts/
  seed.py               — 10 categories + 31 outlets (incl. Hacker News), MBFC leaning data
sources/
  feeds.opml            — RSS/Atom feeds: BBC, Al Jazeera, DW, France 24, The Guardian (×5),
                          ProPublica, The Intercept
tests/
  conftest.py           — async test client, per-session test DB
  test_health.py        — GET /health smoke test
  test_auth.py          — register, duplicate email, login, wrong password, /me
docker-compose.yml      — FastAPI, PostgreSQL (pgvector), Redis, Celery worker, Celery beat
Dockerfile              — python:3.12-slim, pre-downloads all-MiniLM-L6-v2 + en_core_web_sm
pyproject.toml          — all deps, ruff/black/pytest config, semantic-release config
Makefile                — up, down, build, test, lint, format, migrate, migration, seed
.env.example            — copy to .env, set credentials
.github/workflows/
  ci.yml                — lint → test → release (semantic-release on push to main)
LICENSE                 — AGPL-3.0
```

**Tests have not been run yet** — the test database requires a running PostgreSQL instance. Run `make test` after the local Docker environment is up.

---

### VPS — live

| Property | Value |
|---|---|
| Provider | Hetzner Cloud |
| Type | CPX32 (4 vCPU AMD EPYC, 8GB RAM, 160GB SSD) |
| OS | Ubuntu 24.04 LTS |
| Location | Helsinki (hostname: `vernier-prod-cpx32-hel1`) |
| IP | 95.217.177.243 |
| SSH | Key-only auth, password auth disabled, root login disabled |
| Firewall | UFW active — ports 22, 80, 443 only |
| User | `deploy` (sudo) |
| Docker | 29.5.1 |
| Services | All running: api, postgres, redis, worker, beat |
| Migrations | 0001–0004 applied |
| Seed data | Loaded (categories + outlets incl. Hacker News) |
| Health check | `curl http://localhost:8000/health` → `{"status":"ok","version":"0.1.0"}` |

**Upgrade path:** CPX32 → CPX41 (16GB) before Phase 3 when Ollama moves to the VPS.

---

### GitHub

| Property | Value |
|---|---|
| Repo | `care-git/vernier-news` |
| Visibility | Public (AGPL-3.0) |
| CI | Lint → Test → Release (python-semantic-release) |
| Versioning | Conventional Commits; `feat:` bumps minor, `fix:` bumps patch, `BREAKING CHANGE` bumps major |

---

### Domain

| Property | Value |
|---|---|
| Domain | `vernier.news` |
| Registrar | Cloudflare |
| DNS | A record `@` → 95.217.177.243 (proxied), A record `www` → 95.217.177.243 (proxied) |
| Status | Propagated and live |

---

### Email (Resend)

| Property | Value |
|---|---|
| Provider | Resend |
| Domain | `vernier.news` |
| Status | Verified and ready to send |

---

## Phase 1 — data pipeline

Steps 1–7 are complete. Step 8 (OpenClaw integration) is the immediate next task.

### Completed steps

1. **NormalisedArticle + normalise()** — `app/pipeline/ingestion/normalise.py`
2. **RSS/OPML ingestion** — `app/pipeline/ingestion/rss.py`; domain-based outlet lookup via OPML `domain` attribute
3. **Deduplication + embeddings** — `app/pipeline/dedup.py`; sentence-transformers `all-MiniLM-L6-v2` (384-dim), URL dedup then cosine < 0.01 within 72h
4. **Clustering** — `app/pipeline/clustering.py`; spaCy NER + pgvector cosine + Jaccard, combined score threshold 0.45
5. **Categorisation** — `app/pipeline/categorise.py`; Ollama (Mistral 7B), graceful failure if Ollama is unavailable
6. **Redis caching** — `app/cache/clusters.py` + `app/cache/digest.py`; `cluster_summary:{id}` and `digest:{user_id}`, 1h TTL
7. **Celery tasks + API connectors** — `app/pipeline/tasks.py`; 5 tasks, 6 API connectors. Beat schedule:
   - `ingest_feeds` + `categorise_pending` every 30 minutes
   - `precompute_cluster_summaries` + `precompute_digests` every hour

### API connector key status

| Connector | Key needed | Where to set |
|---|---|---|
| GDELT | No | — |
| Hacker News | No | — |
| Guardian | Yes — `GUARDIAN_API_KEY` | VPS `.env` |
| GNews | Yes — `GNEWS_API_KEY` | VPS `.env` |
| Currents | Yes — `CURRENTS_API_KEY` | VPS `.env` |
| NYT | Yes — `NYT_API_KEY` | VPS `.env` |

GDELT and HN are active immediately. The others activate once their key is present in `.env` — no code changes needed.

### Step 8 — OpenClaw integration (next task)

OpenClaw provides structured outlet metadata (ownership, funding, country). The integration will:
- Fetch the OpenClaw dataset
- Match outlets in the DB by domain
- Populate ownership/funding fields (to be added to the `Outlet` model)

See `PROJECT.md` Section 4 for the full spec.

### After Phase 1

Before starting Phase 2, do a smoke test to confirm the pipeline is running end-to-end:

```bash
ssh deploy@95.217.177.243
docker compose exec worker celery -A app.worker:celery_app call pipeline.ingest_feeds
# then check logs:
docker compose logs --tail=50 worker
```

If `ingest_feeds` is logging saved article counts, the pipeline is working.

---

## Immediate next steps

1. **OpenClaw integration** (Phase 1, Step 8) — see above
2. **Add API keys to VPS `.env`** — Guardian, GNews, Currents, NYT (optional but recommended)
3. **Run `make test`** — tests have never been run; need a local Docker environment up
4. **Start UK Ltd incorporation** — lead time is weeks; needed before Stripe in Phase 4. Doesn't block Phase 2 or 3.

---

## Key decisions already made

These are settled — not open questions:

- **Auth:** JWT only (Argon2 + PyJWT). Google OAuth deferred to Phase 4.
- **Translation:** OPUS-MT (self-hosted, free) in Phase 4. DeepL upgrade in Phase 5.
- **Entity resolution:** spaCy native EntityLinker + custom Wikidata KnowledgeBase. Not spacy-entity-linker (stale, experimental).
- **Influence graph:** Cytoscape.js via Flutter HtmlElementView.
- **Podcast transcripts:** Podcasting 2.0 namespace (primary source) + local Whisper (cited as generated). No third-party transcript services.
- **Political leaning seed data:** MBFC public dataset. Acknowledged explicitly in soft launch materials.
- **Wire propagation:** Four-tier detection system. Phase 1 logs tiers only — collapsing activates in Phase 3 after empirical calibration.
- **Embeddings:** `all-MiniLM-L6-v2` (384-dim, pre-downloaded in Dockerfile). Pre-downloaded into image at build time to avoid cold-start latency.
- **Clustering score:** 0.6 × cosine + 0.4 × Jaccard, threshold 0.45. Entity cache stored as JSONB on `Cluster` to avoid a separate entity mentions table.
- **Categorisation:** Ollama on VPS (Phase 3+). Phase 1 uses `http://localhost:11434` — will fail silently if unavailable. Articles remain uncategorised and are retried on next `categorise_pending` run.
- **Free tier article selection:** Representative Article Score (RAS) — 6 dimensions including political centroid proximity to prevent systematic bias.
- **Social platforms:** Bluesky + Mastodon in Phase 4. LinkedIn + X/Twitter deferred to Phase 5/6.
- **Payments:** Stripe. Requires UK Ltd to be in place first.
- **Email:** Resend. Domain verified.
