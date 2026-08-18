# Vernier News

[![CI](https://github.com/care-git/vernier-news/actions/workflows/ci.yml/badge.svg)](https://github.com/care-git/vernier-news/actions/workflows/ci.yml)
[![Licence: AGPL-3.0-or-later](https://img.shields.io/badge/licence-AGPL--3.0--or--later-blue.svg)](LICENSE)
![Version](https://img.shields.io/badge/version-0.30.1-informational)
![Status](https://img.shields.io/badge/status-pre--alpha-orange)

A global media intelligence platform. The aim is for this to not only act as a news aggregator but as 
an analytical layer that maps **who covers a story, from what political position, with what ownership relationships, 
and with what coverage distribution across the world**. The name comes from the vernier scale.

> ### Development status
>
> **This is pre-alpha software, roughly a quarter of the way through its MVP build (ish).** 
> There is no public product yet: the backend runs 24/7 on a VPS and ingests news continuously,
> but the user-facing digest is deliberately frozen (see [Known limitations](#known-limitations))
> and the Flutter client is not publicly deployed. 
>
> Nothing here should be treated as stable, and the schemas, thresholds, and APIs are all subject to change.
>
> **Pace, August 2026:** active development is paused/slowed while I'm focusing more on full-time job applications.
> The deployment will stay live and ingesting and the build will resume after.

---

## Contents

- [Where the project actually is](#where-the-project-actually-is)
- [What works today](#what-works-today)
- [Known limitations](#known-limitations)
- [Architecture](#architecture)
- [The pipeline](#the-pipeline)
- [Repository layout](#repository-layout)
- [Running it locally](#running-it-locally)
- [Diagnostics and maintenance](#diagnostics-and-maintenance)
- [Roadmap](#roadmap)
- [Design documents](#design-documents)
- [Contributing](#contributing)
- [Disclaimer](#ai-disclaimer)
- [Licence](#licence)

---

## Where the project actually is

The build is sequenced in phases, MVP-first.

| Phase | Scope | Status |
|---|---|---|
| **Phase 0, Foundation** | FastAPI skeleton, Postgres + pgvector schema, Redis, Celery, JWT auth, Docker Compose, CI, VPS deployment, HTTPS | Complete, deployed |
| **Phase 1, Data pipeline** | Ingestion (RSS/OPML + 6 API connectors), normalisation, dedup, embeddings, clustering, precompute cache, developer monitoring | Complete, running live |
| **Phase 2, MVP clients** | Flutter Web PWA (auth → onboarding → digest → cluster detail), pipeline-quality rework, categorisation, Python CLI client | **In progress** currently paused |
| **Phase 3, Hardening** | Rate limiting, test coverage, DB indexes, monitoring, error-handling consistency, wire-tier collapsing | Not started |
| **Phases 4+, Full product** | Entity resolution, influence graph, translation, social sources, full-text collection, payments | Not started |

Phase 2 stalled deliberately: mid-phase it became clear that clustering and corpus quality had to be
fixed before any client screen was worth looking at, so the work since late July 2026 has been
pipeline-side (corpus hygiene, syndication capture, outlet discovery, entity persistence) rather
than UI.

## What works today

**Backend (live on a Hetzner CPX32, behind Caddy with auto-renewing TLS):**

- **Ingestion**: RSS/Atom via a curated OPML library, plus connectors for the Guardian, GNews,
  Currents, NYT, GDELT and Hacker News. URLs are canonicalised, recurring formats (live blogs,
  briefings, crosswords) are classified out of story clustering, and every distinct URL form for an
  article is recorded as a *sighting* so syndication paths survive deduplication.
- **Outlet discovery**: outlets are created as they are discovered rather than filtered against a
  seed list, with country resolved to ISO 3166, registrable domain derived via the public suffix
  list, and a source type classified per domain. The corpus has grown from 31 seeded outlets to
  thousands.
- **Embeddings**: `bge-m3` (multilingual, 1024-dim), stored in pgvector with an HNSW index. The
  same embedding substrate serves dedup, clustering, and the categorisation design.
- **Deduplication**: URL dedup then cosine similarity within a 72-hour window, plus four-tier wire
  propagation detection (logged, not yet collapsing).
- **Clustering**: spaCy NER plus a pgvector candidate search, joined on a semantic-primary score:
  nearest-member similarity above a high threshold, or above a mid threshold when entity overlap
  corroborates it (with a floor of two shared entities). Entity mentions are persisted at ingest.
- **Tunable thresholds**: every clustering, dedup, and wire-tier threshold lives in a database
  `settings` table, so calibration is a data change, not a redeploy.
- **Caching**: Redis-backed precompute of cluster summaries and per-user digests.
- **API**: JWT auth (Argon2 + PyJWT), plus articles, clusters (summary + detail with full member
  source list and country counts), outlets, users/preferences, digest, and key-guarded admin
  endpoints. Live health check: `https://vernier.news/health`.
- **Telegram control bot**: deterministic and LLM-free: `/health`, `/ingest`, `/clusters`,
  `/sources`, plus a daily health digest and threshold alerts for queue depth, ingestion stall and
  API-unreachable. Replaced an earlier LLM agent gateway, which cost far more than four fixed
  operations justified and wasn't cool enough to warrant the additional expense and complexity.

**Client - Flutter Web PWA, runs locally against the live API (not publicly deployed):**

- Login/register, a three-step onboarding flow, a category-grouped digest with pull-to-refresh, and
  a cluster detail screen with a political spread bar, coverage chips, and per-source outlet cards.
- Bloc/Cubit state management, `go_router` routing with an auth/onboarding redirect guard, `dio`
  with transparent JWT refresh-and-retry, `get_it` DI.

**Engineering:**

- CI on every push and PR: `ruff` + `black`, then ~70 tests against a pgvector service container,
  then `python-semantic-release`. Conventional Commits drive versioning; 15 Alembic migrations to
  date.

## Known limitations

These are known and documented in keeping with the project's principle of transparency.

- **The digest is deliberately frozen.** It groups clusters by category, and categorisation has
  never run in production (the original design needed a 7B local LLM that does not fit an 8 GB
  VPS), so every article is uncategorised and users see an empty state. Unfreezing needs a
  category-independent "Top stories" group (or hopefully full categorisation), which is the next 
  milestone I am working on.
- **Categorisation is being replaced, not merely deferred.** The new design is embedding-driven:
  broad categories assigned to clusters by centroid similarity, plus an emergent topic hierarchy,
  with a small local model used only to *label* topics.
- **Clustering has a chaining problem.** Articles match a cluster by nearest *member*, which under
  single linkage chains loosely-related articles into mega-clusters. The planned fix is centroid
  matching. A separate ~6–14% of articles are under-grouped, addressable by threshold calibration.
- **A high singleton rate is mostly legitimate.** ~84% of clusters hold one article, which looks
  like a bug but isn't, thankfully. Singleton rate tracks coverage overlap, and there are simply
  more niche outlets producing unique stories than I initially anticipated. 
  Cluster coherence and under-grouping are the metrics that matter here, not the singleton count.
- **The corpus is politically skewed.** As of the last audit the article-weighted spectrum ran roughly
  53% centre-left, 45% centre, 1% centre-right, with no genuinely far-left or far-right sources.
  Every downstream "spread" visualisation is only as agnostic as that distribution, so closing the
  curation gap is another key task I am looking at, with the primary issue being that pulling from 
  more sources gets vastly more expensive than is feasible for me currently.
- **Roughly half of articles are RSS summaries only** (< 200 characters of body). This does not
  harm clustering, but it will cap categorisation depth until full-text collection lands in
  Phase 4.
- **Phase 3 concerns are outstanding by design.** These being rate limiting, broader test coverage, 
  index tuning, production monitoring, and API error-handling consistency, and they are all scheduled 
  for attention in the future.

## Architecture

| Layer | Choice |
|---|---|
| API | FastAPI (Python 3.12), Uvicorn |
| Database | PostgreSQL 16 + pgvector, SQLAlchemy 2 async, Alembic |
| Cache / broker | Redis 7 |
| Background jobs | Celery + Celery Beat |
| Embeddings | `bge-m3` via sentence-transformers (1024-dim, HNSW index) |
| NLP | spaCy NER, langdetect, BeautifulSoup/lxml |
| Auth | JWT (PyJWT) with Argon2 password hashing |
| Client | Flutter (Dart) - Web/PWA first, then mobile and desktop |
| Ops | Docker Compose, Caddy (auto-TLS), single Hetzner VPS |
| Monitoring | Telegram control bot (`python-telegram-bot`) |
| CI/CD | GitHub Actions, ruff, black, pytest, python-semantic-release |

## The pipeline

```
feeds + APIs  →  normalise  →  dedup + embed  →  cluster  →  precompute cache  →  API  →  clients
  RSS/OPML       HTML strip     URL + cosine     spaCy NER    Redis summaries     FastAPI   Flutter PWA
  6 connectors   language       wire tiers       pgvector KNN  + user digests               (CLI planned)
  outlet         detection      sightings        semantic +
  discovery      canonical URL                   entity score
```

Celery Beat runs ingestion (and, eventually, categorisation) every 30 minutes, and the precompute
passes hourly.

## Repository layout

```
app/            FastAPI application
  auth/           JWT auth: router, hashing, dependencies
  models/         SQLAlchemy models (article, outlet, cluster, entity, category, user, settings)
  schemas/        Pydantic response contracts shared with every client
  routers/        articles, clusters, outlets, users, digest, admin
  pipeline/       ingestion (+ connectors), normalise, dedup, embedding, clustering, tuning, tasks
  cache/          Redis precompute for cluster summaries and digests
bot/            Telegram control bot (own minimal Docker image, no ML dependencies)
client/         Flutter Web PWA
migrations/     Alembic migrations
scripts/        Diagnostic, calibration and backfill scripts
sources/        feeds.opml - the curated feed library
docs/           Design specifications
tests/          pytest suite (API, pipeline, bot)
```

## Running it locally

**Prerequisites:** Docker and Docker Compose; Python 3.12 for tooling outside containers; Flutter
3.44+ to run the client.

```bash
cp .env.example .env
```

Fill in at minimum `JWT_SECRET_KEY` (`openssl rand -hex 32`) and the Postgres credentials. Every
API connector key is optional (connectors without a key are skipped, and GDELT and Hacker News need none).

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
make up
make migrate
make seed
```

The API is then at `http://localhost:8000`, with interactive docs at `/docs`.

Run the client against it:

```bash
cd client && flutter run -d chrome --web-port=8080 --dart-define=API_BASE_URL=http://localhost:8000
```

Add `http://localhost:8080` to `CORS_ORIGINS` in `.env` first, or the browser will block the calls.

Tests and linting:

```bash
make test
make lint
```

`make test` needs Postgres (with the `vector` extension) and Redis reachable per `.env`

## Diagnostics and maintenance

All run inside the `api` container as `python -m scripts.<name>`, most exposed as `make` targets:

| Command | What it does |
|---|---|
| `make analyse` | Read-only corpus audit: composition, source health, language mix, political-leaning coverage, wire tiers, cluster-size distribution, similarity distributions, index health |
| `make spotcheck` | Qualitative sample of real clusters and singletons, to judge clustering by eye |
| `make recluster` | **Destructive.** Wipes clusters and rebuilds from scratch under current settings |
| `make reembed` | Resumable backfill for articles with no embedding; run after any embedding-model change |
| `make classify-outlets` | Backfills registrable domain and source type for existing outlets |
| `make mark-repeats`, `make backfill-sightings`, `make backfill-gdelt` | Corpus backfills for recurring formats, URL sightings, and GDELT history |
| `scripts/check_feed.py URL …` | Feed liveness checker used to vet candidate RSS URLs before adding them to `sources/feeds.opml` |

Threshold calibration is a loop: update a row in the `settings` table, then `make recluster` and
`make analyse`. No redeploy, because thresholds are data.

## Roadmap

Next, in order, when work resumes:

1. **Centroid matching** for cluster joins, plus a rebuild harness that faithfully mirrors live
   dormancy.
2. **Threshold calibration** against the reclustering harness.
3. **Unfreeze the digest** with a category-independent "Top stories" group. This will be the first real 
   content on screen, and the first time the cluster detail view is reachable end to end.
4. **Embedding-driven categorisation** at cluster level.
5. **Preferences screen** and a **Python CLI client** with full parity to the PWA.

Beyond the MVP is the following: entity resolution against Wikidata, computed political leaning across three axes,
the influence graph, self-hosted translation, institutional social sources, and polite full-text collection.

## Design documents

The specifications under [`docs/`](docs/) carry the reasoning behind the current build:

- [`docs/data-model.md`](docs/data-model.md) - aggregation levels, the Thread layer, and capture policy
- [`docs/clustering-fix-spec.md`](docs/clustering-fix-spec.md) - the clustering rework (partly superseded; read its amendment note first)
- [`docs/categorisation-design.md`](docs/categorisation-design.md) - the embedding-driven categorisation replacement
- [`docs/political-leaning-design.md`](docs/political-leaning-design.md) - computed leaning across three axes, replacing hardcoded scores
- [`docs/telegram-bot-spec.md`](docs/telegram-bot-spec.md) - the monitoring bot

## Contributing

The project is open source by necessity: a platform that calculates political leanings and assesses
source independence cannot ask users to trust a black box. Issues and pull requests are welcome,
though responses will be slow while development is paused.

Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`,
`docs:`, `chore:` and so on, and `python-semantic-release` derives every version and changelog
entry from them).

## AI Disclaimer

AI has been used in the creation of this project.

All AI work that is publicly released is reviewed (and normally edited) by me, the author, William (Billy) Jecks. 

## Licence

AGPL-3.0-or-later. See [LICENSE](LICENSE).
Commercial licensing available, please contact billy@jecks.co.uk.
