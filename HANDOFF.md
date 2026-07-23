# Vernier News — Handoff Document

*Last updated: 23 July 2026*

---

## What this project is

Vernier News is a global media intelligence platform. Not a news aggregator — an analytical layer that maps who covers stories, from what political position, with what ownership relationships, and with what coverage distribution across the world. The name comes from the vernier scale: the precision mechanism that measures what blunt instruments miss.

Full concept: `CONCEPT.md`. Full build plan: `PROJECT.md`. Both are v0.4, approved for development.

---

## Git workflow — mandatory reading for all contributors and Claude instances

### Conventional Commits

All commit messages must follow the **Conventional Commits** standard. Every message takes the form:

```
<type>(<optional scope>): <short description>
```

The type controls how semantic-release bumps the version:

| Type | Meaning | Version bump |
|---|---|---|
| `feat:` | New feature | **MINOR** `1.4.2 → 1.5.0` |
| `fix:` | Bug fix | **PATCH** `1.4.2 → 1.4.3` |
| `feat!:` or footer `BREAKING CHANGE:` | Breaks backwards compatibility | **MAJOR** `1.4.2 → 2.0.0` |
| `chore:` | Maintenance, no production change | no release |
| `docs:` | Documentation only | no release |
| `style:` | Formatting, whitespace | no release |
| `refactor:` | Code restructured, no new features/fixes | no release |
| `test:` | Adding or updating tests | no release |
| `build:` | Build system, dependencies | no release |
| `ci:` | CI pipeline changes | no release |
| `perf:` | Performance improvement | patch |

**Golden rule: one logical change per commit.** If you find yourself writing "and" in the description, it should be two commits. Semantic-release reads every commit individually — one `feat:` among ten `fix:` commits still triggers a minor bump for that release.

### No committing from Claude

Claude Code instances do **not** have access to the SSH passphrase and must never attempt to run `git commit`, `git push`, or any destructive git operation. After making code changes, output the exact commands for the developer to run:

```
git add <specific files>
git commit -m "<type>(<scope>): <description>"
git push
```

Break changes into separate commits where the type or scope differs. Do not batch unrelated changes into one commit.

---

## Current state

### Phase 0 — complete and deployed

Phase 0 is fully running on the VPS. Health check passes, all migrations are applied, seed data loaded.

**Working directory:** `/Users/billy/Projects/vernier/`

```
app/
  main.py               — FastAPI app, all routers registered, CORS via settings.cors_origins,
                          /health endpoint
  config.py             — pydantic-settings, extra="ignore" for POSTGRES_* vars,
                          cors_origins setting (comma-separated string)
  database.py           — async SQLAlchemy engine with NullPool, Base, get_db dependency
  worker.py             — Celery app (celery_app), Beat schedule, autodiscover pipeline tasks
  redis_client.py       — aioredis client singleton
  auth/
    router.py           — POST /api/v1/auth/register, /login, /refresh
    utils.py            — Argon2 password hashing, JWT create/decode
    dependencies.py     — get_current_user FastAPI dependency
    schemas.py          — RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
  models/
    article.py          — Article (pgvector embedding, wire_tier, category_id, author,
                          collection_source as Text)
    outlet.py           — Outlet (political_leaning_lr float, wire_service bool)
    cluster.py          — Cluster (entity_cache JSONB) + ArticleCluster join table
    category.py         — Category (name, slug)
    user.py             — User (UserTier StrEnum) + UserPreferences (JSONB)
    settings.py         — Setting (typed key/value store for pipeline tuning thresholds)
  schemas/
    cluster.py          — PoliticalSpread, ClusterSummary, ClusterDetail (member sources +
                          country counts) Pydantic response models
    outlet.py           — OutletSummary, OutletDetail (Pydantic response models)
    digest.py           — DigestResponse (Pydantic response model)
    user.py             — UserPreferencesRequest, UserPreferencesResponse
  routers/
    articles.py         — GET /articles/, GET /articles/{id} (auth required)
    clusters.py         — GET /clusters/ (ClusterSummary list); GET /clusters/{id}
                          (ClusterDetail: summary + full member source list + country counts)
    outlets.py          — GET /outlets/, GET /outlets/{id} (public)
    users.py            — GET /users/me; PUT /users/preferences (upsert, auth required)
    digest.py           — GET /digest/ — serves cached DigestResponse or empty payload
    admin.py            — GET /admin/health, POST /admin/ingest, GET /admin/clusters/stats,
                          GET /admin/sources (X-Admin-Key header auth, fails closed if key unset)
  pipeline/
    tasks.py            — 5 Celery tasks; each pipeline run calls tuning.refresh() first
    tuning.py           — PipelineTuning dataclass + loader; thresholds from the settings table
    dedup.py            — sentence-transformers embed, URL+cosine dedup, wire tier detection
                          (thresholds via tuning)
    clustering.py       — spaCy NER, pgvector candidate search, Jaccard+cosine scoring
                          (thresholds via tuning; being reworked — docs/clustering-fix-spec.md)
    categorise.py       — Ollama (Mistral 7B) — being superseded by embedding-based
                          categorisation (docs/categorisation-design.md)
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
    20260517_0001_initial_schema.py                        — full MVP schema, pgvector extension
    20260519_0002_add_author_wire_tier_wire_service.py
    20260519_0003_add_cluster_entity_cache.py
    20260519_0004_add_article_category_id.py
    20260519_0005_widen_collection_source.py               — VARCHAR(50) → Text
    20260723_0006_add_settings_table.py                    — pipeline tuning key/value + seed
bot/                    — Telegram control bot (replaces OpenClaw); LLM-free, long-polling
  config.py             — BotConfig (pydantic-settings); allowlist parsing
  admin_client.py       — async httpx wrapper over /admin/* (typed AdminError)
  formatting.py         — JSON → Telegram HTML
  auth.py               — allowlist message filter (fail-closed)
  handlers.py           — /health /ingest /clusters /sources /help /start + error handler
  alerts.py             — daily digest + threshold alerts (queue depth, stall, API-down)
  main.py               — wiring; refuses to start without token + allowlist
  Dockerfile            — minimal py3.12-slim image (no ML deps)
openclaw/               — DECOMMISSIONED (cost). Skill files kept as endpoint-contract record
  skills/
    vernier-{health,ingest,clusters,sources}/  — AgentSkill wrappers (legacy)
client/                 — Flutter Web PWA (Phase 2)
  lib/
    main.dart           — entry point; calls configureDependencies() then runApp
    app.dart            — StatefulWidget; calls AuthCubit.checkAuth() in initState;
                          BlocProvider.value(AuthCubit) wrapping MaterialApp.router
    core/
      api/
        api_client.dart       — Dio wrapper; get/getList/post/put methods; debug logging in dev
        api_exception.dart    — typed ApiException (statusCode + message)
        auth_interceptor.dart — injects JWT; handles 401 → refresh → retry cycle
        endpoints.dart        — all endpoint paths as constants; baseUrl via --dart-define
      di/
        injection.dart        — get_it; registers SharedPreferences, ApiClient,
                                AuthRepository, AuthCubit, PreferencesRepository,
                                OnboardingCubit, DigestRepository, DigestCubit,
                                ClusterRepository, ClusterCubit (factory)
      models/
        cluster_summary.dart  — ClusterSummary + PoliticalSpread (mirrors backend schema)
        cluster_detail.dart   — ClusterDetail + ClusterSource + ClusterSourceOutlet + CountryCount
        digest_response.dart  — DigestResponse (mirrors backend schema)
        outlet.dart           — OutletSummary + OutletDetail (mirrors backend schema)
        token_response.dart   — TokenResponse
        user.dart             — UserModel
        user_preferences.dart — UserPreferences (purpose, interests, depthPreference)
      repositories/
        auth_repository.dart       — login/register/getCurrentUser/saveTokens/clearTokens/hasToken
        cluster_repository.dart    — getCluster(id) → ClusterDetail
        digest_repository.dart     — getDigest() → DigestResponse
        preferences_repository.dart — updatePreferences() → PUT /users/preferences
      router/
        app_router.dart            — GoRouter; all routes wired; auth + onboarding redirect guard
        go_router_refresh_stream.dart — ChangeNotifier adapter for cubit streams
      theme/
        app_theme.dart        — Material 3 light + dark themes; seed Color(0xFF1A3050)
      widgets/
        spread_bar.dart       — shared political-spread bar (used by digest + cluster views)
    features/
      auth/
        bloc/
          auth_cubit.dart     — checkAuth/login/register/logout/completeOnboarding
          auth_state.dart     — sealed: AuthInitial, AuthLoading, AuthAuthenticated(isNewUser),
                                AuthUnauthenticated(error?)
        screens/
          login_screen.dart   — email + password form; error banner; link to register
          register_screen.dart — email + password + confirm form; link to login
      onboarding/
        bloc/
          onboarding_cubit.dart  — submit(purpose, interests, depthPreference) / skip()
          onboarding_state.dart  — sealed: OnboardingInitial, Loading, Complete, Error
        screens/
          onboarding_screen.dart — 3-step PageView: purpose → categories → depth;
                                   animated SelectCards + FilterChips; skip saves defaults
      digest/
        bloc/
          digest_cubit.dart   — load() / refresh(); DigestInitial/Loading/Loaded/Empty/Error
          digest_state.dart   — sealed states
        screens/
          digest_screen.dart  — category-grouped ListView; pull-to-refresh; ClusterCard widget;
                                 uses shared SpreadBar; empty + error states
      clusters/
        bloc/
          cluster_cubit.dart  — load(id) → ClusterInitial/Loading/Loaded/Error
          cluster_state.dart  — sealed states
        screens/
          cluster_screen.dart — headline, meta, SpreadBar, coverage chips, source list;
                                 tap a source → outlet inline card (bottom sheet) + open article
  web/
    index.html          — PWA entry point; updated title + description
    manifest.json       — PWA manifest; name "Vernier News"; theme #1A3050
  pubspec.yaml          — flutter_bloc, go_router, dio, shared_preferences, get_it, intl,
                          url_launcher
scripts/
  seed.py               — 10 categories + 31 outlets (incl. Hacker News), MBFC leaning data
sources/
  feeds.opml            — RSS/Atom feeds: BBC, Al Jazeera, DW, France 24, The Guardian (×5),
                          ProPublica, The Intercept
tests/
  conftest.py           — NullPool engine, sync setup_db (asyncio.run), per-test async session
  test_health.py        — GET /health smoke test
  test_auth.py          — register, duplicate email, login, wrong password, /me
  test_tuning.py        — PipelineTuning defaults + settings-table overlay
Caddyfile               — vernier.news → api:8000, www redirect, auto-TLS via Let's Encrypt
docker-compose.yml      — Caddy, FastAPI, PostgreSQL (pgvector), Redis, Celery worker, Celery beat,
                          Telegram bot (behind the `bot` profile)
                          Production config only — no --reload, no volume mount
docker-compose.override.yml.example
                        — Dev overrides template: adds --reload + ./app volume mount to api.
                          Copy to docker-compose.override.yml locally (gitignored).
Dockerfile              — python:3.12-slim, pre-downloads all-MiniLM-L6-v2 + en_core_web_sm
pyproject.toml          — all deps, ruff/black/pytest config, semantic-release config
Makefile                — up, down, build, test, lint, format, migrate, migration, seed
.env.example            — copy to .env, set credentials; includes CORS_ORIGINS
docs/
  telegram-bot-spec.md      — Telegram control bot spec
  clustering-fix-spec.md    — clustering over-fragmentation diagnosis + fix plan
  categorisation-design.md  — embedding-driven categorisation design
.github/workflows/
  ci.yml                — lint → test → release (semantic-release on push to main)
LICENSE                 — AGPL-3.0
```

---

### CI — fully passing

All three CI jobs pass on push to `main`:

| Job | Status | Notes |
|---|---|---|
| Lint | ✅ Passing | ruff + black |
| Test | ✅ Passing | 8 tests, pgvector/pgvector:pg16 service container |
| Release | ✅ Passing | python-semantic-release v9, current version `0.15.1` |

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
| Services | All running: caddy, api, postgres, redis, worker, beat, bot |
| Migrations | 0001–0006 applied |
| Seed data | Loaded (categories + outlets incl. Hacker News) |
| Health check | `curl https://vernier.news/health` → `{"status":"ok","version":"0.1.0"}` |
| HTTPS | Live via Caddy + Let's Encrypt. Cert auto-renews. |
| Code | **Up to date with `main`** (v0.15.1) — settings table (migration 0006), cluster detail endpoint, and per-service restart policies all deployed. |

**Upgrade path (revised):** A VPS upgrade is **no longer planned**. The categorisation redesign (embedding-driven; `docs/categorisation-design.md`) fits the current 8GB CPX32 — no on-box 7B Ollama. Larger Hetzner instances (CX4x/CAX) have been perpetually out of stock and steeply price-hiked, so the architecture is designed to stay on the CPX32.

After deploying, confirm `CORS_ORIGINS=https://vernier.news` is set in the VPS `.env` (the default is correct but should be explicit).

#### Caddy — operational notes

- **Caddyfile:** `~/vernier-news/Caddyfile` (version controlled), mounted read-only into the caddy container
- **Certificates:** stored in `caddy_data` Docker named volume — persists across `docker compose down/up`
- **Logs:** `docker compose logs caddy`
- **Cloudflare SSL mode:** must remain **Full** (not Flexible) — Flexible would have Cloudflare skip cert validation, Full enforces HTTPS to origin
- If the cert ever fails to renew, check that ports 80 and 443 are reachable and that Cloudflare is not caching `.well-known/acme-challenge/` paths (it doesn't by default)

#### Docker/UFW — critical note for all infrastructure changes

Docker writes iptables rules directly, bypassing UFW entirely. A `ports:` entry in `docker-compose.yml` exposes that port to the internet regardless of UFW rules. The current configuration is intentional:

| Service | Host binding | Reason |
|---|---|---|
| caddy | `0.0.0.0:80`, `0.0.0.0:443` | Must be public — serves HTTPS |
| api | `127.0.0.1:8000` | Loopback only — accessed via Caddy within Docker network |
| postgres | none | Internal Docker network only |
| redis | none | Internal Docker network only |

**Never add `ports:` to postgres or redis.** If a service needs to communicate with another service, use the Docker service name (e.g., `api:8000`, `redis:6379`) — all compose services share a network automatically.

**Note on port scanners:** Hetzner operates a network-level SYN proxy for DDoS protection that completes TCP handshakes on behalf of the server for all ports. External port scanners (nmap, etc.) will report every port as "open" regardless of what is actually listening. Verify real port exposure via `ss -tlnp` and `sudo iptables -t nat -S` from within the VPS, not from external scans.

#### Restart policy — all services

Every service in `docker-compose.yml` sets `restart: unless-stopped`, so the full stack recovers automatically after a reboot or Docker daemon restart. (Historically only `caddy` had this, which left api/postgres/redis/worker/beat down after a reboot on 23 July 2026 — fixed by adding the policy to all services.)

---

### GitHub

| Property | Value |
|---|---|
| Repo | `care-git/vernier-news` |
| Visibility | Public (AGPL-3.0) |
| CI | Lint → Test → Release (python-semantic-release) |
| Versioning | Conventional Commits — see Git workflow section above |

---

### Domain

| Property | Value |
|---|---|
| Domain | `vernier.news` |
| Registrar | Cloudflare |
| DNS | A record `@` → 95.217.177.243 (proxied), A record `www` → 95.217.177.243 (proxied) |
| Status | Propagated and live. `www` redirects to apex via Caddy. |

---

### Email (Resend)

| Property | Value |
|---|---|
| Provider | Resend |
| Domain | `vernier.news` |
| Status | Verified and ready to send |

---

## Phase 1 — data pipeline — complete

All 8 steps complete and verified live on VPS. Pipeline running: **35,931 articles, 21,329 clusters, 31 outlets active** (as of 23 July 2026). The cluster/article ratio (~1.7) reveals over-fragmentation — clustering is being reworked (see Outstanding issues and `docs/clustering-fix-spec.md`).

### Completed steps

1. **NormalisedArticle + normalise()** — `app/pipeline/ingestion/normalise.py`
2. **RSS/OPML ingestion** — `app/pipeline/ingestion/rss.py`; domain-based outlet lookup via OPML `domain` attribute
3. **Deduplication + embeddings** — `app/pipeline/dedup.py`; sentence-transformers `all-MiniLM-L6-v2` (384-dim), URL dedup then cosine < 0.01 within 72h. Embedding model being upgraded to **bge-m3** (multilingual, 1024-dim) — see `docs/clustering-fix-spec.md`.
4. **Clustering** — `app/pipeline/clustering.py`; spaCy NER + pgvector cosine + Jaccard, combined score threshold 0.45. Thresholds now in the `settings` table (`app/pipeline/tuning.py`); scoring being reworked to semantic-primary — see `docs/clustering-fix-spec.md`.
5. **Categorisation** — `app/pipeline/categorise.py`; Ollama (Mistral 7B). **Never ran on the VPS** (no Ollama), so all articles are uncategorised. Being **replaced** by embedding-driven categorisation — see `docs/categorisation-design.md`.
6. **Redis caching** — `app/cache/clusters.py` + `app/cache/digest.py`; `cluster_summary:{id}` and `digest:{user_id}`, 1h TTL
7. **Celery tasks + API connectors** — `app/pipeline/tasks.py`; 5 tasks, 6 API connectors. Beat schedule:
   - `ingest_feeds` + `categorise_pending` every 30 minutes
   - `precompute_cluster_summaries` + `precompute_digests` every hour
8. **Developer monitoring interface** — Telegram control bot `@vernier_monitor_bot` (`bot/`): four commands (health, ingest, clusters, sources) mapping to `/admin/*`, plus a daily digest and threshold alerts. Runs as a Docker Compose service behind the `bot` profile. Replaced the original LLM-driven OpenClaw gateway, decommissioned on cost — see operational notes below.

### API connector key status

| Connector | Key needed | Where to set |
|---|---|---|
| GDELT | No | — |
| Hacker News | No | — |
| Guardian | Yes — `GUARDIAN_API_KEY` | VPS `.env` ✓ |
| GNews | Yes — `GNEWS_API_KEY` | VPS `.env` ✓ |
| Currents | Yes — `CURRENTS_API_KEY` | VPS `.env` ✓ |
| NYT | Yes — `NYT_API_KEY` | VPS `.env` ✓ |

### Telegram control bot — operational notes

Replaced the OpenClaw gateway on 23 July 2026. OpenClaw's per-message LLM agent loop (`anthropic/claude-haiku-4-5`) burned credits far faster than its value justified for four fixed operations. The bot is deterministic — slash commands map straight to the existing `/admin/*` endpoints, no LLM — so ongoing cost is ~£0. Full spec: `docs/telegram-bot-spec.md`.

- **Service:** Docker Compose service `bot`, gated behind the `bot` profile (`COMPOSE_PROFILES=bot` in the VPS `.env`). Long-polling only — no exposed ports; reaches the API over the internal Docker network at `http://api:8000`.
- **Logs:** `docker compose logs bot`
- **Commands:** `/health`, `/ingest`, `/clusters`, `/sources`, `/help`
- **Alerting:** daily health digest at `BOT_DIGEST_UTC_HOUR` (UTC) + a threshold poll every `BOT_ALERT_POLL_MINUTES` covering queue depth, ingestion stall, and API-unreachable (each alert de-duplicated: one on entry, one on recovery). Sent to `TELEGRAM_ALERT_CHAT_ID`; alerting is disabled if that is unset.
- **Access control:** allowlist via `TELEGRAM_ALLOWED_USER_IDS` — fail-closed; an empty allowlist means the bot refuses to start.
- **Config (VPS `.env`):** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USER_IDS`, `TELEGRAM_ALERT_CHAT_ID`, `BOT_API_BASE_URL` (default `http://api:8000`), `BOT_DIGEST_UTC_HOUR`, `BOT_ALERT_POLL_MINUTES`, `BOT_QUEUE_DEPTH_THRESHOLD`, `BOT_INGEST_STALL_HOURS`. Reuses the existing `ADMIN_API_KEY` for the `X-Admin-Key` header.
- **BotFather:** command menu set via `/setcommands` (see the spec for the list).
- **OpenClaw:** `openclaw-gateway` systemd `--user` service stopped and disabled. The `openclaw/skills/` files remain in the repo as a record of the endpoint contract; the install can be removed from the VPS whenever convenient.

### Known fixes applied during Phase 1

- `app/database.py` — `NullPool` added to prevent asyncio event loop conflicts between Celery tasks and the SQLAlchemy async engine
- `app/models/article.py` — `collection_source` widened from `String(50)` to `Text`; RSS ingestion stores full feed URLs (`rss:<url>`) which exceeded the original limit. Migration `0005` applied.
- `Makefile` — `migrate`, `migration`, and `seed` targets updated to run via `docker compose exec api` (alembic is not installed on the VPS host)
- `tests/conftest.py` — NullPool on the test engine + synchronous `setup_db` using `asyncio.run()` to prevent cross-event-loop asyncpg errors; `CREATE EXTENSION IF NOT EXISTS vector` added before `create_all`
- `pyproject.toml` — `build_command = ""` (empty string) to skip PSR build step; `B008` added to ruff ignore list (FastAPI `Depends()` in default args is intentional)

---

## Pre-Phase 2 hardening — complete (20 May 2026)

### Security fixes

- **Redis/PostgreSQL internet-exposed** — Docker's iptables bypass was exposing both services publicly despite UFW rules. Fixed by removing `ports:` from both services in `docker-compose.yml`. Flagged by BSI/CERT-Bund via Hetzner abuse notification.
- **API internet-exposed** — `ports: "8000:8000"` changed to `"127.0.0.1:8000:8000"`, binding only to loopback. Caddy accesses the API via the internal Docker network (`api:8000`).
- **Admin key guard fails open** — `app/routers/admin.py` condition `if settings.admin_api_key and key != ...` replaced with `if not settings.admin_api_key or key != ...` so the guard fails closed when the key is absent.
- **SQL NULL/boolean comparisons** — `Article.category_id == None` → `.is_(None)` and `Cluster.active == True` → `.is_(True)` in `app/routers/admin.py` and `app/routers/clusters.py`. Python equality against SQL NULL evaluates to UNKNOWN, silently returning wrong rows.

### Infrastructure additions

- **Caddy reverse proxy** — added as a Docker service. Handles TLS termination with auto-renewing Let's Encrypt certificate. `vernier.news` proxies to `api:8000` within the Docker network; `www.vernier.news` issues a permanent redirect to the apex.
- **CORS** — `allow_origins=["*"]` tightened to a configurable list via `settings.cors_origins` (`CORS_ORIGINS` env var, comma-separated, defaults to `https://vernier.news`).

---

## Phase 2 — MVP Clients — in progress

### Completed

**Infrastructure cleanup (22 May 2026)**

- `docker-compose.yml` stripped of dev-only config (`--reload`, `./app` volume mount). These now live in `docker-compose.override.yml` (gitignored). Copy `docker-compose.override.yml.example` to `docker-compose.override.yml` for local development — `docker compose up` picks it up automatically.

**Backend — API contract (22 May 2026)**

- `app/schemas/` package added: `ClusterSummary`, `PoliticalSpread`, `OutletSummary`, `OutletDetail`, `DigestResponse` Pydantic models define the API contract for all Phase 2 clients.
- `GET /api/v1/digest/` now serves the cached `DigestResponse` from Redis (or an empty payload if the cache hasn't run yet).
- `GET /api/v1/clusters/` and `GET /api/v1/clusters/{id}` return `ClusterSummary` shapes; detail endpoint falls back to minimal DB data on cache miss.
- `GET /api/v1/outlets/` and `GET /api/v1/outlets/{id}` use `OutletSummary`/`OutletDetail` schemas.

**Backend — user preferences (22 July 2026)**

- `app/schemas/user.py` added: `UserPreferencesRequest`, `UserPreferencesResponse`.
- `PUT /api/v1/users/preferences` — upserts a `UserPreferences` row; stores `purpose` and `interests` list in the `categories` JSONB column, `depth_preference` as a string. Returns the saved values.

**Flutter client — scaffold and API layer (22 May 2026)**

- Flutter SDK installed at `~/flutter/bin/flutter` (Channel stable, 3.44.0, darwin-arm64).
- Chromium installed at `/Applications/Chromium.app`; `CHROME_EXECUTABLE` and Flutter PATH set in `~/.zshrc`.
- `client/` Flutter project created (`news.vernier` org, `vernier_news` package, web platform).
- Architecture: Bloc/Cubit state management, `go_router` navigation, `dio` HTTP client, `shared_preferences` token storage, `get_it` DI.
- `lib/core/api/` — `ApiClient` (Dio wrapper: get/getList/post/put), `AuthInterceptor` (JWT attach + 401 refresh/retry), `ApiException`, `Endpoints`.
- `lib/core/models/` — `ClusterSummary`, `PoliticalSpread`, `DigestResponse`, `OutletSummary`, `OutletDetail`, `UserModel`, `TokenResponse`, `UserPreferences`.
- `lib/core/theme/app_theme.dart` — Material 3 light/dark, seed `Color(0xFF1A3050)`.

**Flutter client — auth feature (22 July 2026)**

- `AuthRepository` — login/register/getCurrentUser/token persistence (SharedPreferences keys `access_token`, `refresh_token`).
- `AuthCubit` — `checkAuth` / `login` / `register` / `logout` / `completeOnboarding`. Sealed `AuthState` with `AuthAuthenticated(isNewUser)`.
- `GoRouterRefreshStream` — adapts the cubit stream to `ChangeNotifier` for go_router's `refreshListenable`.
- Router redirect guard — unauthenticated users → `/login`; new users → `/onboarding`; established users on auth/onboarding routes → `/digest`.
- Login and register screens — Material 3 forms with validation, error banners, and password visibility toggle.
- `app.dart` converted to `StatefulWidget`; `checkAuth()` called in `initState`; `BlocProvider.value` provides `AuthCubit` to the tree.
- End-to-end tested: login → digest, register → onboarding flows verified live against VPS.

**Flutter client — onboarding feature (22 July 2026)**

- `PreferencesRepository` — wraps `PUT /users/preferences`.
- `OnboardingCubit` — `submit(purpose, interests, depthPreference)` / `skip()`. Calls `authCubit.completeOnboarding()` on success, triggering the router redirect to `/digest`.
- 3-step `PageView` screen: purpose selection (4 animated SelectCards), category multi-select (FilterChip grid, pre-seeded from purpose choice), depth preference (3 options). Skip saves defaults.
- End-to-end tested: onboarding completion → digest redirect verified live.

**Flutter client — digest view (22 July 2026)**

- `DigestRepository` — wraps `GET /digest/`.
- `DigestCubit` — `load()` (initial) / `refresh()` (pull-to-refresh). States: Initial, Loading, Loaded, Empty, Error.
- `DigestScreen` — category-grouped `ListView.builder`; `RefreshIndicator`; empty state (digest not yet populated) and error state with retry button.
- `ClusterCard` widget — headline (2 lines), source count + independent count, relative age, countries. Taps navigate to `/cluster/:id`.
- Logout button in app bar calls `AuthCubit.logout()`.

**Backend + Flutter — cluster detail view (23 July 2026)**

- `GET /api/v1/clusters/{id}` upgraded to return `ClusterDetail` (summary fields + full member source list with outlet name/country/leaning/parent-org/wire-tier + `country_counts`). Summary fields from cache; member list on-demand from the DB.
- Flutter cluster detail screen (`features/clusters/`): headline, meta, shared `SpreadBar`, coverage chips, source list; tapping a source opens an outlet inline card (bottom sheet) with a "Read original article" button (`url_launcher`). `SpreadBar` extracted to `core/widgets/` and shared with the digest.
- **Not yet testable end-to-end** — blocked by the empty digest (see Outstanding issues); reachable only once clusters surface.

**Pipeline — settings table (23 July 2026)**

- `settings` table (migration 0006) + `app/pipeline/tuning.py`: all clustering/dedup/wire-tier thresholds are now live-editable rows, loaded at task start with code-default fallback. Behaviour-preserving (seeded values == old constants). Foundation for recalibration after the embedding upgrade.

**Infrastructure — restart policies (23 July 2026)**

- Added `restart: unless-stopped` to all `docker-compose.yml` services (previously only caddy + bot had it), so the stack survives reboots. Found when a VPS reboot left only caddy + bot running.

### Remaining Phase 2 work

**Active workstream — pipeline rework** (a prerequisite that emerged during Phase 2: the digest is empty and clusters are over-fragmented, so the pipeline is reworked before more client features):

1. **bge-m3 embedding upgrade** — multilingual 1024-dim, int8 ONNX (`docs/clustering-fix-spec.md`)
2. **Clustering fix** — semantic-primary scoring, entity de-brittling, threshold recalibration, consolidation pass
3. **Categorisation** — embedding-driven broad categories (cluster-level) + emergent topic tree + small local LLM labelling (`docs/categorisation-design.md`)
4. **Unfreeze the digest** — a category-independent "Top stories" group + real category groups once categorisation works

**Then the remaining client features:**

5. **User preferences screen** — category management, depth preference, account settings (email, password change)
6. **Python CLI client** — `pip install vernier-news`, `digest` / `cluster` / `outlet` / `search` / `prefs`, full parity with PWA

(Cluster detail view — **done** this session, backend + Flutter; see Completed above.)

---

## Local Flutter development

**Prerequisites:** Flutter SDK on `PATH` (set in `~/.zshrc`), Chromium at `/Applications/Chromium.app`, `CHROME_EXECUTABLE` pointing to Chromium binary in `~/.zshrc`.

**Development setup — backend on VPS (current workflow):**

The backend runs permanently on the VPS at `https://vernier.news`. No local Docker needed for day-to-day Flutter development.

Add your Flutter dev server port to `CORS_ORIGINS` in the VPS `.env`:
```
CORS_ORIGINS=https://vernier.news,http://localhost:8080
```
Then restart the API: `docker compose restart api` (SSH into VPS).

**Run the Flutter app against the VPS:**
```bash
cd client
CHROME_EXECUTABLE=/Applications/Chromium.app/Contents/MacOS/Chromium \
flutter run -d chrome --web-port=8080 --dart-define=API_BASE_URL=https://vernier.news
```

**Alternative — run the backend locally** (useful when making backend changes):
```bash
# From repo root, requires docker-compose.override.yml to exist
make up
```
Add `http://localhost:8080` to `CORS_ORIGINS` in your local `.env`, then:
```bash
flutter run -d chrome --web-port=8080 --dart-define=API_BASE_URL=http://localhost:8000
```

**Build for production:**
```bash
cd client
flutter build web --dart-define=API_BASE_URL=https://vernier.news
```
Output at `client/build/web/` — static files to be served by Caddy.

---

## Immediate next steps

1. **bge-m3 embedding upgrade** (step 1 of `docs/clustering-fix-spec.md`) — swap the embedding model to bge-m3 (int8 ONNX), migrate `Article.embedding` to `Vector(1024)`, rebuild the HNSW index, and re-embed the corpus. Touches the live pipeline + Docker image; do on a branch and run the re-embed off-peak.
2. **Clustering rework + recalibration** — rescore (semantic-primary), de-brittle entity overlap, recalibrate thresholds in the `settings` table, add the consolidation pass to collapse the 21k singletons.
3. **Categorisation** then **unfreeze the digest** (per `docs/categorisation-design.md`).
4. **Start UK Ltd incorporation** — lead time is weeks; needed before Stripe in Phase 4. Does not block the current work.

---

## Outstanding issues

### Active — pipeline rework (blocking the digest)

- **Digest is empty.** Three compounding causes: (a) the precompute cache is empty on the VPS — `/health` shows `cluster summaries cached: 0` and `digests cached: 0`, so the hourly `precompute_*` jobs aren't populating Redis (investigate worker/beat logs; the 21k-cluster summary job is likely too heavy / failing); (b) the digest groups by category via an inner join; and (c) all articles are uncategorised. The digest is deliberately left "frozen" until categorisation works — a "Top stories" fallback + real categories will unfreeze it.
- **Clustering over-fragmentation.** 21,329 clusters from 35,931 articles (~1.7/cluster) — mostly singletons. Root cause: exact-string entity-Jaccard at 0.4 weight drags related articles below the 0.45 join threshold; MiniLM is English-centric. Fix plan: `docs/clustering-fix-spec.md`.
- **Categorisation gap.** Ollama never ran on the VPS. Being **replaced** (not deferred) by embedding-driven categorisation: `docs/categorisation-design.md`.

### Defer to Phase 3 — already planned

Everything flagged in the codebase audit (rate limiting, test coverage, DB indexes, monitoring, Swagger in production, Redis TTL tuning, password strength validation, API error handling consistency) is an explicit Phase 3 deliverable per `PROJECT.md`. Do not pull this work forward — Phase 3 is the right time to calibrate against real load data.

---

## Key decisions already made

These are settled — not open questions:

- **Auth:** JWT only (Argon2 + PyJWT). Google OAuth deferred to Phase 4.
- **Reverse proxy:** Caddy. Auto-TLS, minimal config, single binary. Certificate stored in `caddy_data` Docker volume.
- **Translation:** OPUS-MT (self-hosted, free) in Phase 4. DeepL upgrade in Phase 5.
- **Entity resolution:** spaCy native EntityLinker + custom Wikidata KnowledgeBase. Not spacy-entity-linker (stale, experimental).
- **Influence graph:** Cytoscape.js via Flutter HtmlElementView.
- **Podcast transcripts:** Podcasting 2.0 namespace (primary source) + local Whisper (cited as generated). No third-party transcript services.
- **Political leaning seed data:** MBFC public dataset. Acknowledged explicitly in soft launch materials.
- **Wire propagation:** Four-tier detection system. Phase 1 logs tiers only — collapsing activates in Phase 3 after empirical calibration. Thresholds live in the `settings` table (`app/pipeline/tuning.py`).
- **Pipeline tuning:** clustering, dedup, and wire-tier thresholds live in the `settings` table, loaded via `app/pipeline/tuning.py` with code defaults as fallback. Enables calibration without redeploys.
- **Embeddings:** **being upgraded** from `all-MiniLM-L6-v2` (384-dim) to **bge-m3** (multilingual, 1024-dim, int8 ONNX; ~1.5–2GB RAM). Multilingual is the key gain (clustering/categorisation across languages). Shared substrate for dedup, clustering, and categorisation. See `docs/clustering-fix-spec.md`.
- **Clustering score:** originally 0.6 × cosine + 0.4 × Jaccard, threshold 0.45 — **being reworked** to semantic-primary with entity overlap as a booster (the exact-Jaccard term caused over-fragmentation). Entity cache stored as JSONB on `Cluster`. See `docs/clustering-fix-spec.md`.
- **Categorisation:** **superseded.** No on-box 7B Ollama. Two-layer, embedding-driven, low-bias: a small curated set of broad categories (assigned to clusters by centroid similarity) + a fully-emergent topic hierarchy (BERTopic-style over cluster centroids), with a **small local LLM (Qwen2.5-1.5B, Apache-2.0) for topic labelling only** — free to run, no per-call cost. Categorise at the **cluster** level. Broad-category list finalised after the topic tree is built. See `docs/categorisation-design.md`.
- **Free tier article selection:** Representative Article Score (RAS) — 6 dimensions including political centroid proximity to prevent systematic bias.
- **Social platforms:** Bluesky + Mastodon in Phase 4. LinkedIn + X/Twitter deferred to Phase 5/6.
- **Payments:** Stripe. Requires UK Ltd to be in place first.
- **Email:** Resend. Domain verified.
- **Ollama on VPS:** **abandoned for categorisation.** A 7B model doesn't fit the 8GB CPX32, and larger Hetzner instances are perpetually out of stock + steeply price-hiked. The embedding-driven design fits the current box; only a small (1.5B) local model is used, for labelling. True model "learning" would be later embedding fine-tuning on a rented GPU, not an on-box LLM.
- **Flutter state management:** Bloc with Cubit for simpler screens. Strict separation of events, states, and business logic.
- **Flutter navigation:** go_router. URL-based routing for web; all routes defined in `AppRoute` constants.
- **Flutter HTTP:** dio. `AuthInterceptor` handles JWT attachment and 401 → refresh → retry transparently.
- **Flutter environment config:** `--dart-define=API_BASE_URL=<url>` at build/run time. Default is `https://vernier.news`.
- **Dev CORS:** `CORS_ORIGINS` env var (comma-separated). Add `http://localhost:5173` locally; VPS keeps `https://vernier.news` only.
