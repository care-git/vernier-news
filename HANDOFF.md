# Vernier News — Handoff Document

*Last updated: May 2026*

---

## What this project is

Vernier News is a global media intelligence platform. Not a news aggregator — an analytical layer that maps who covers stories, from what political position, with what ownership relationships, and with what coverage distribution across the world. The name comes from the vernier scale: the precision mechanism that measures what blunt instruments miss.

Full concept: `CONCEPT.md`. Full build plan: `PROJECT.md`. Both are v0.4, approved for development.

---

## Current state

### Phase 0 — complete (code)

All Phase 0 code deliverables are written and in `/Users/billy/Projects/spider/`:

```
app/
  main.py           — FastAPI app, all routers registered, CORS, /health endpoint
  config.py         — pydantic-settings config from .env
  database.py       — async SQLAlchemy engine, Base, get_db dependency
  worker.py         — Celery app (vernier_news), broker/backend = Redis
  auth/
    router.py       — POST /api/v1/auth/register, /login, /refresh
    utils.py        — Argon2 password hashing, JWT create/decode
    dependencies.py — get_current_user FastAPI dependency
    schemas.py      — RegisterRequest, LoginRequest, TokenResponse
  models/
    article.py      — Article (pgvector embedding col, wire_flag, outlet FK)
    outlet.py       — Outlet (political_leaning_lr float, MBFC-sourced)
    cluster.py      — Cluster + ArticleCluster join table
    category.py     — Category (name, slug)
    user.py         — User (UserTier enum) + UserPreferences (JSONB)
  routers/
    articles.py     — GET /articles/, GET /articles/{id} (auth required)
    clusters.py     — GET /clusters/, GET /clusters/{id} (auth required)
    outlets.py      — GET /outlets/, GET /outlets/{id} (public)
    users.py        — GET /users/me (auth required)
    digest.py       — GET /digest/ stub (Phase 2 deliverable)
migrations/
  env.py            — async Alembic env, reads DATABASE_URL from settings
  versions/
    20260517_0001_initial_schema.py — full MVP schema, pgvector extension
scripts/
  seed.py           — loads 10 categories + 30 outlets with MBFC leaning data
tests/
  conftest.py       — async test client, per-session test DB setup/teardown
  test_health.py    — GET /health smoke test
  test_auth.py      — register, duplicate email, login, wrong password, /me
docker-compose.yml  — FastAPI, PostgreSQL (pgvector/pgvector:pg16), Redis,
                      Celery worker, Celery beat. Ollama excluded (runs locally).
Dockerfile          — python:3.12-slim, installs pyproject.toml deps
pyproject.toml      — package: vernier-news, all deps, ruff/black/pytest config
Makefile            — up, down, build, test, lint, format, migrate, migration, seed
.env.example        — copy to .env, set POSTGRES_PASSWORD + JWT_SECRET_KEY
.github/workflows/
  ci.yml            — lint (ruff, black) → test (pytest + postgres + redis service)
LICENSE             — AGPL-3.0
```

**Tests have not been run yet** — the test database requires a running PostgreSQL instance. Run `make test` after the VPS or local Docker environment is up.

---

### VPS — provisioned and hardened

| Property | Value |
|---|---|
| Provider | Hetzner Cloud |
| Type | CPX32 (4 vCPU AMD EPYC, 8GB RAM, 160GB SSD) |
| OS | Ubuntu 24.04 LTS |
| Location | (your chosen DC — Falkenstein or Helsinki) |
| SSH | Key-only auth, password auth disabled, root login disabled |
| Firewall | UFW active — ports 22, 80, 443 only |
| User | `deploy` (sudo) |

**Upgrade path:** CPX32 → CPX41 (16GB) when Hetzner stock allows, via Hetzner console resize (reboot required, no data migration). Do this before Phase 3 when Ollama moves to the VPS.

---

### External track — outstanding

These are not yet done. None block Phase 0 code work, but some block later phases:

| Action | Blocks | Notes |
|---|---|---|
| **GitHub repo** (`vernier-news`) | Pushing code, CI/CD | Create repo, `git init` locally, push |
| **Domain registration** | Resend verification, Let's Encrypt | Required before custom email sending address works |
| **Resend account + domain verification** | Phase 2 (password reset email) | DNS propagation takes time — do early |
| **UK Ltd incorporation** | Phase 4 (Stripe goes live) | Lead time is weeks. Start now, runs in parallel |

---

## Immediate next steps

These complete Phase 0 on the VPS before Phase 1 begins:

### 1 — Install Docker on the VPS

```bash
ssh deploy@<your-vps-ip>
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker deploy
# log out and back in for group membership to take effect
docker --version
```

### 2 — Copy the project to the VPS

Once the GitHub repo exists this becomes `git clone`. Until then, use rsync:

```bash
rsync -av --exclude='.git' --exclude='__pycache__' --exclude='.venv' \
  /Users/billy/Projects/spider/ deploy@<your-vps-ip>:~/vernier-news/
```

### 3 — Configure environment

```bash
ssh deploy@<your-vps-ip>
cd ~/vernier-news
cp .env.example .env
nano .env
```

Set at minimum:
- `POSTGRES_PASSWORD` — something strong
- `JWT_SECRET_KEY` — generate with `openssl rand -hex 32`

### 4 — Start services and verify

```bash
make up
make migrate
make seed
curl http://localhost:8000/health
# expected: {"status":"ok","version":"0.1.0"}
```

### 5 — Push code to GitHub

```bash
# locally
git init
git add .
git commit -m "Phase 0: foundation"
git remote add origin git@github.com:<your-username>/vernier-news.git
git push -u origin main
```

CI will run on push — lint then test. Tests require the PostgreSQL service defined in `ci.yml` and will run automatically.

---

## Phase 1 — what comes next

Once Phase 0 is verified running on the VPS, Phase 1 (Data Pipeline) begins. Key deliverables:

- RSS/Atom feed ingestion with feedparser
- sentence-transformers `all-MiniLM-L6-v2` embeddings at ingest
- spaCy NER pipeline
- Article deduplication via cosine similarity
- Four-tier wire propagation detection (Tier 0: known wire services; Tier 1: >0.88 similarity within 6h; Tier 2: 0.70–0.88 + time/byline; Tier 3: review queue)
- Celery Beat scheduled ingestion jobs
- GNews, Currents, NYT, BBC API connectors
- Clustering pipeline (HDBSCAN or similar)
- Ollama (Mistral 7B Q4_K_M) running locally for categorisation

Full Phase 1 spec: `PROJECT.md` Section 4.

---

## Key decisions already made

These are settled — not open questions:

- **Auth:** JWT only (Argon2 + PyJWT). Google OAuth deferred to Phase 4.
- **Translation:** OPUS-MT (self-hosted, free) in Phase 4. DeepL upgrade in Phase 5.
- **Entity resolution:** spaCy native EntityLinker + custom Wikidata KnowledgeBase. Not spacy-entity-linker (stale, experimental).
- **Influence graph:** Cytoscape.js via Flutter HtmlElementView.
- **Podcast transcripts:** Podcasting 2.0 namespace (primary source) + local Whisper (cited as generated). No third-party transcript services.
- **Political leaning seed data:** MBFC public dataset. Acknowledged explicitly in soft launch materials.
- **Wire propagation:** Four-tier system with database-stored thresholds, monthly calibration review.
- **Free tier article selection:** Representative Article Score (RAS) — 6 dimensions including political centroid proximity to prevent systematic bias.
- **Social platforms:** Bluesky + Mastodon in Phase 4. LinkedIn + X/Twitter deferred to Phase 5/6.
- **Payments:** Stripe. Requires UK Ltd to be in place first.
- **Email:** Resend. Requires domain verification.

---

## Working directory note

The local working directory is `/Users/billy/Projects/spider` — a legacy name from before the project was named. The package, repo, and all identifiers use `vernier-news`. The directory itself has not been renamed.
