# Project Document — Vernier News

### From Concept to Execution

*Working Document — v0.4 — May 2026* *Reference document: CONCEPT.md v0.4*

---

## How to Read This Document

CONCEPT.md defines what this platform is, why it exists, and what it must do. This document defines how it gets built — the technical decisions, the sequenced phases, and the risks that need managing. All technical decisions are confirmed and documented within their relevant phase sections. The risk register and remaining action items (Section 8\) cover what still needs attention before and during the build.

The phase plan is structured in two parts. Part A is the MVP execution plan — a solo developer working primarily full-time can have a working product in real users' hands within 5–7 months. Part B is the full product roadmap, built iteratively on the proven MVP foundation. No Part B work begins until the MVP is running and generating real user feedback.

The document is structured to be useful at every stage of development. The phase plan tells you what to build and in what order, with all key decisions documented within each phase. The risk register tells you what to watch.

---

## 1\. Project Summary

### What is being built

A global information landscape platform that collects news and information from tens of thousands of sources, clusters related reporting, and gives users the analytical tools to understand the full context of how any story is being reported — who is covering it, from what position, with what relationships, and with what distribution across the world. The platform serves users from casual daily readers to enterprise research teams, on iOS, Android, macOS, Windows, and Linux CLI, from a single backend hosted on a VPS.

### Guiding constraints

- Every design and implementation decision must be interrogatable against the core principles in CONCEPT.md Section 2  
- No platform version is secondary — CLI parity with GUI is a hard requirement  
- The architecture must be correct for enterprise scale from day one, even if the initial deployment is personal  
- All collection must respect `robots.txt`, crawl delays, and terms of service  
- Every data point presented to users must have a traceable, documented source

### Developer context

Solo engineer. Cybersecurity graduate (BSc, De Montfort University). Prior project: anomaly-based ML network detection pipeline in Python — demonstrates strong Python, ML, modular architecture, CLI tooling, and testing skills. New territory: web API development, Flutter/Dart, Docker, full-stack deployment, payment processing, legal and business structure.

Working primarily full-time on this project, with some hours each week committed to job searching. Part-time employment provides baseline income. If full-time employment begins during the build, all phase timelines approximately double. The architecture accommodates an interrupted build pace.

### Current status

Pre-development. Concept phase complete. Project plan restructured to MVP-first approach. No code written. No infrastructure deployed. All technical decisions are confirmed — Phase 0 can begin. Legal entity formation (UK Ltd) should start in parallel during Phases 0–2; see Section 8 for remaining action items.

---

## 2\. Confirmed Technical Stack

These decisions are made. They are not open questions.

### Backend

| Component | Choice | Purpose |
| :---- | :---- | :---- |
| API framework | FastAPI (Python) | Core API layer serving all clients |
| Primary database | PostgreSQL \+ pgvector | Articles, clusters, entities, feature analysis, embeddings |
| Cache \+ queue broker | Redis | Pre-computed layer caching, Celery job queue |
| Task queue | Celery | Scheduled and background jobs |
| Embedding model | sentence-transformers `all-MiniLM-L6-v2` | Article embeddings for clustering and dedup |
| NER pipeline | spaCy | Entity extraction at ingest |
| Entity resolution | spaCy native EntityLinker with custom Wikidata KnowledgeBase | Canonical entity identity across languages |
| Local LLM serving | Ollama | Categorisation, feature analysis signals, summary generation |
| Web crawler | Scrapy \+ Playwright/Playwright-stealth | Polite scraping for Layer 4 sources |
| Translation | OPUS-MT (Helsinki-NLP, self-hosted) → DeepL API (Phase 5+) | Machine translation; OPUS-MT in Phase 4 (free, local); DeepL introduced in Phase 5 once revenue supports it |
| Orchestration agent | OpenClaw | Human-facing monitoring and control interface; custom AgentSkills trigger pipeline operations and surface system health via chat |
| Containerisation | Docker Compose (initial) → Kubernetes (scale) | Service isolation and deployment |

### Frontend

| Component | Choice | Purpose |
| :---- | :---- | :---- |
| GUI framework | Flutter (Dart) | Single codebase compiling to Web/PWA, iOS, Android, macOS, Windows |
| CLI client | Python | Linux terminal client, full feature parity |

### Data sources (confirmed layers)

| Layer | Sources |
| :---- | :---- |
| Layer 1 — Structured feeds | RSS/Atom OPML library, Guardian API, GNews, Currents, NYT API, BBC API (Phases 0–3); NewsAPI.org (Phase 4+, commercial terms required) |
| Layer 2 — Specialist datasets | GDELT, Reddit API, Hacker News API, arXiv, PubMed, SSRN, government feeds, podcast transcripts, Substack/newsletter RSS |
| Layer 3 — Institutional social media | Bluesky, Mastodon (Phase 4); LinkedIn (Phase 5/6, Partner Program application required during Phase 4); X/Twitter (Phase 5/6, cost-justified) |
| Layer 4 — Polite scraping | Scrapy \+ Playwright, `robots.txt` compliant |

### Infrastructure

| Component | Choice | Rationale |
| :---- | :---- | :---- |
| Initial hosting | Single VPS | Personal deployment; correct architecture for later scaling |
| Data warehouse (deferred) | ClickHouse | Analytical query separation; added when query volume justifies |
| Payment processing | Stripe | Subscription billing, geographic tax compliance, currency localisation |
| Version control | Git (open source repository, AGPL licensed) | Public code, community contribution |

---

## 3\. Data Architecture

### Core database schema (high-level)

The following entities form the primary data model. Detailed schema design is a Phase 0 deliverable.

**articles** — id, url, outlet\_id, author\_id, title, body, language, published\_at, collected\_at, collection\_source, translation\_id (nullable), wire\_propagation\_flag, embedding (vector), raw\_html

**clusters** — id, first\_published\_at, last\_updated\_at, total\_source\_count, independent\_source\_count, primary\_category\_id, status (active/dormant/merged), provenance\_root\_id

**article\_cluster\_membership** — article\_id, cluster\_id, joined\_at, independence\_score

**outlets** — id, name, domain, parent\_org\_id (nullable), country, language\_primary, rss\_feed\_url, feature\_analysis (jsonb), wikidata\_qid (nullable)

**authors** — id, name, outlets (array of outlet\_ids), wikidata\_qid (nullable), feature\_analysis (jsonb), political\_leaning (jsonb)

**organisations** — id, name, wikidata\_qid, parent\_org\_id (nullable), org\_type (media\_company / government / ngo / corporation / other), feature\_analysis (jsonb)

**entities** — id, canonical\_name, wikidata\_qid, entity\_type (person / org / government / place / company), aliases (array), profile (jsonb), confidence\_score

**entity\_article\_mentions** — entity\_id, article\_id, surface\_form, resolution\_confidence, position\_in\_text

**entity\_relationships** — entity\_id\_a, entity\_id\_b, relationship\_type, documented\_source, valid\_from, valid\_to (nullable)

**stakeholder\_entries** — id, cluster\_id, entity\_id, stake\_type (financial / political / legal / regulatory), documented\_source, description

**translations** — id, article\_id, source\_language, translated\_body, translation\_engine, llm\_review\_flags (jsonb), confidence\_level, created\_at

**user\_preferences** — user\_id, categories (array), sub\_niches (array), depth\_preference, digest\_time, notification\_settings (jsonb), tier

**social\_media\_sources** — id, platform, account\_handle, account\_name, account\_category (government / media\_org / journalist / ngo / corporation / official\_body), wikidata\_qid (nullable), verified, active

### Embedding and vector search

pgvector stores article embeddings directly in PostgreSQL. Similarity queries for clustering and deduplication run as vector operations within the database. This avoids the operational overhead of a separate vector store (Pinecone, Weaviate, etc.) at the cost of some performance at extreme scale. The tradeoff is appropriate for the early and growth phases; a dedicated vector store can be introduced if query latency becomes a constraint.

### The two-layer compute model

**Pre-computed layer (Redis-cached)**

- Daily user digests per preference profile  
- Story cluster summaries (headline, source count, category, political spread, geographic spread)  
- Feature analysis snapshots per outlet, author, and organisation  
- Coverage distribution snapshots per category and region  
- Influence graph snapshots (top-level, for fast surface rendering)

**Analytical layer (on-demand, PostgreSQL)**

- Full article cluster access with all member articles  
- Deep provenance chains  
- Historical entity tracking  
- Complex influence graph traversal with filters  
- Bulk export queries  
- Multi-entity correlation searches

The two layers never share compute. Analytical queries run against read replicas or the data warehouse when that layer is introduced. Casual users never wait on analytical workloads.

---

## 4\. Development Phases

### Context and approach

This plan is written for a solo developer working primarily full-time on the project, with some hours each week committed to job searching. Time estimates assume roughly 30–35 productive hours per week. If full-time employment begins during development, all timelines approximately double — but progress remains progress, and the architecture is designed to accommodate an interrupted build pace.

The plan is structured in two parts. **Part A** is the MVP execution plan: the smallest version of the platform that delivers the core value proposition and can be in real users' hands. It excludes a significant portion of the features in CONCEPT.md by design. **Part B** is the full product roadmap: the complete feature set built iteratively on top of the proven MVP foundation. No Part B work begins until the MVP is running, gathering real user feedback, and demonstrating that the core concept works in practice.

### What the MVP includes and deliberately excludes

The core value of this platform — the thing that makes someone want to use it on day one — is this: *I can see how different outlets are covering the same story, with basic context about those outlets.* Everything else is depth on top of that foundation. The MVP delivers exactly that and nothing more.

**MVP includes:** RSS/Atom feed ingestion, GDELT as supplementary source, deduplication, clustering, basic categorisation, pre-seeded political leaning data (imported from public sources, not computed), basic outlet profiles, Flutter Web PWA, Python CLI, user accounts and preferences.

**MVP deliberately excludes:** custom political leaning NLP calculation, entity knowledge graph and Wikidata linking, influence graph visualisation, ownership tree, framing divergence, coverage distribution, stakeholder analysis, story provenance visualisation, narrative evolution timeline, translation pipeline, social media sources, Stripe and payment tiers, native app builds, email/SMS notifications, enterprise API.

None of the excluded features are abandoned — they are sequenced into Part B after the MVP proves the concept.

### Overview

| Part | Phase | Name | Primary Focus | Solo Dev Estimate |
| :---- | :---- | :---- | :---- | :---- |
| A | 0 | Foundation | Infrastructure, schema, API skeleton | 3–4 weeks |
| A | 1 | Data Pipeline | Ingestion, processing, clustering, caching | 6–8 weeks |
| A | 2 | MVP Clients | Flutter PWA \+ Python CLI | 7–10 weeks |
| A | 3 | Hardening & Soft Launch | Stability, testing, first real users | 4–5 weeks |
| B | 4 | Feature Layer 1 | Analytics depth, Stripe, first revenue | 10–14 weeks |
| B | 5 | Feature Layer 2 | Native apps, full visualisations, public launch | 10–14 weeks |
| B | 6 | Enterprise & Scale | GraphQL API, enterprise tier, Kubernetes | Ongoing |

**Realistic total to soft launch (end of Phase 3): 5–7 months at primary focus pace.** **Realistic total to public commercial launch (end of Phase 5): 14–20 months.**

The trigger to move from Part A to Part B is not a calendar date — it is evidence. The MVP must be in real users' hands, generating real feedback, and demonstrating that the core clustering and outlet context features are genuinely useful before any Part B feature work begins.

---

## Part A — MVP Execution Plan

---

### Phase 0 — Foundation

**Goal:** A correctly running empty system. No features. Every service isolated. Development environment identical to production environment from day one.

**Duration:** 3–4 weeks

**Learning investment this phase:** Docker and Docker Compose (the most important new skill to invest in properly), FastAPI basics, PostgreSQL setup and Alembic migrations. None of this is far from your existing Python knowledge. Expect the first week to be mostly learning; the second week to be productive.

**Parallel activity:** Begin Flutter and Dart learning now, not when you need it. Spend an hour each evening on Flutter tutorials during Phases 0 and 1\. By the time Phase 2 starts, you will have 10–15 weeks of ambient learning behind you rather than starting Dart cold.

**Deliverables:**

*Infrastructure*

- Hetzner CX41 VPS provisioned (4 vCPU, 16GB RAM, 160GB SSD, \~£13/month — Helsinki or Falkenstein data centre for European data residency and GDPR alignment). During Phases 0–1, Ollama runs locally on the M1 MacBook rather than the VPS, reducing RAM requirements and cost at the start  
- SSH hardening: key-only auth, password auth disabled, firewall rules (ports 22, 80, 443 only)  
- Docker Compose configuration with all services isolated: FastAPI, PostgreSQL (with pgvector), Redis, Celery worker, Celery beat scheduler  
- Ollama excluded from Docker Compose at this stage — runs locally during development  
- Environment variable management via `.env` files; no secrets committed to version control  
- **Resend account created and domain verified during Phase 0.** Password reset emails are a Phase 2 deliverable; Resend requires domain verification (DNS record propagation) before a custom sending address works. Register the project domain and complete Resend domain verification during Phase 0 infrastructure setup — not during Phase 2 when it is first needed  
- Automated PostgreSQL backups to Hetzner Object Storage (S3-compatible, cheap)

*Database — MVP schema* The MVP schema is intentionally smaller than the full schema in Section 3\. Tables for features not in the MVP are not created yet — the schema grows with the product.

articles         — id, url, outlet\_id, title, summary, body, language,

                   published\_at, collected\_at, collection\_source,

                   wire\_flag, embedding vector(384)

outlets          — id, name, domain, country, language\_primary,

                   political\_leaning\_lr float, political\_leaning\_source,

                   parent\_org\_name, rss\_feed\_url, active

clusters         — id, first\_published\_at, last\_updated\_at, category\_id,

                   total\_source\_count, independent\_source\_count, active

article\_cluster  — article\_id, cluster\_id, independence\_score float,

                   joined\_at

categories       — id, name, slug

users            — id, email, password\_hash, tier, created\_at, last\_login

user\_preferences — user\_id, categories jsonb, depth\_preference varchar,

                   digest\_time time, notification\_settings jsonb

- Alembic configured for migrations — schema changes are always versioned, never applied manually  
- pgvector extension installed and smoke-tested  
- Seed data loaded: initial outlet list (\~200 outlets with pre-sourced political leaning data from AllSides/MBFC public datasets), category taxonomy

*API skeleton*

- FastAPI application with routing structure established (routers for: auth, articles, clusters, outlets, users, digest)  
- JWT authentication implemented: email/password only (Argon2 hashing). Token configuration: 7-day access token, 30-day refresh token. Google OAuth deferred to Phase 4 — requires a verified domain and legal entity, which will not be in place until Phase 3/4  
- User registration and login endpoints functional  
- Basic CRUD endpoints for articles, outlets, clusters (no business logic yet — returns empty results)  
- API versioning: all routes under `/api/v1/`  
- OpenAPI docs auto-generated at `/docs`  
- Health check endpoint at `/health`

*Development tooling*

- **Project name decided before Phase 1 begins.** The name is required for: the pip package name and import path, `~/.config/[project]/` CLI config directory, all CLI help text and command invocations, the landing site domain, and the GitHub repository URL. Changing the name after Phase 1 scaffolding is laid means touching every one of these. The name does not need to be final for branding purposes at this stage — it needs to be final for code and infrastructure purposes. Decide it before writing the first line of Phase 1 code

- Git repository initialised, AGPL licence committed  
- GitHub Actions CI/CD: lint (Ruff, Black) → unit tests (pytest) → build check on every push to main  
- pytest configured with initial fixture structure (mirrors the approach from anomaly-detect)  
- Local development environment documented: one-command setup from a fresh clone  
- Makefile or justfile for common dev tasks: `make up`, `make test`, `make migrate`, `make lint`

---

### Phase 1 — Data Pipeline

**Goal:** Articles flowing in, being processed, deduplicated, clustered, categorised, and cached. Nothing is visible to users yet. This is the engine.

**Duration:** 6–8 weeks

**Learning investment this phase:** feedparser and RSS parsing (trivial), sentence-transformers (you understand the ML concepts from your autoencoder work — this is simpler), spaCy NER (straightforward NLP library), Redis as a cache (conceptually simple, a few days), Celery task scheduling (a week to get comfortable). This is the phase most similar to your existing ML work. Expect to move faster here than in Phase 0\.

**Note on Ollama:** During this phase, Ollama continues to run locally on your M1 MacBook for development. Categorisation jobs in development hit your local Ollama instance via the API. On the VPS, categorisation is initially skipped or batch-processed at low frequency until the VPS has Ollama deployed (deferred to Phase 3).

**Deliverables:**

*Ingestion — MVP source layers only*

- RSS/Atom feed parser using feedparser, with OPML library support  
- Initial OPML library: 100–200 curated sources at launch, expanding continuously. Focus on quality over quantity at this stage: major English-language outlets across categories, a selection of regional and international outlets, a set of independent and newsletter sources  
- GDELT connector: near real-time global event data, free, structured  
- Guardian API connector: full article text, generous free tier  
- GNews API connector: headlines and article metadata, free tier sufficient for MVP volume  
- Currents API connector: news headlines and articles, free tier  
- New York Times API connector: article metadata and abstracts, free tier  
- BBC API connector: structured news content  
- Hacker News API connector: technology and policy stories  
- Podcast RSS ingest checks for the **Podcasting 2.0 transcript namespace field** in every feed entry. When a transcript file (SRT, WebVTT, or HTML) is linked in the feed, it is fetched and stored as a primary-source document alongside the episode record. No additional cost; citation is the original feed entry. Coverage varies by podcast but is strong for investigative journalism podcasts  
- All connectors return a normalised article dict; ingestion layer is source-agnostic by design  
- **NewsAPI.org deferred to Phase 4/5.** The free tier explicitly prohibits commercial use. Introducing it during MVP development creates a TOS violation risk once Stripe goes live. GDELT, the OPML library, and the Guardian API provide sufficient MVP coverage. NewsAPI's ~150,000 source index is reintroduced in Phase 4 once commercial API terms can be funded (paid tier ~$449/month)

*Normalisation*

- HTML stripping, encoding normalisation  
- Metadata extraction: author, title, publication date, outlet, URL, language  
- Language detection via langdetect  
- Citation metadata (source, collection method, collected\_at) attached immutably at ingest — never stripped

*Deduplication*

- Embedding generation via sentence-transformers `all-MiniLM-L6-v2` at ingest  
- Cosine similarity via pgvector against recent articles (rolling 72-hour window)  
- Wire propagation detection uses a four-tier system. All thresholds stored in the database settings table and adjustable without code changes. During Phase 1, decisions are logged with full signal sets but not yet acted on — the corpus is too small to calibrate against. Collapsing activates in Phase 3 after empirical review of logged decisions:
  - **Tier 0 — Known wire services:** A `wire_service` flag on the outlets table (AP, Reuters, AFP, PA Media, dpa, and equivalents). Articles from flagged outlets that later appear at >80% similarity at any other outlet are auto-collapsed regardless of timing
  - **Tier 1 — High-confidence wire:** Cosine similarity >0.88 within a 6-hour window → wire copy. At this similarity level, temporal gap is a weak additional signal only
  - **Tier 2 — Probable wire:** Cosine similarity 0.70–0.88 AND (published within 3 hours OR matching author byline) → probable wire copy, collapsed with `wire_confidence: probable`. Counts as 0.25 of an independent source rather than zero
  - **Tier 3 — Suspected, review queue:** Cosine similarity 0.62–0.70 within 4 hours → flagged, not collapsed, surfaced for Phase 3 calibration review. Counts as 0.6 of an independent source
- Phase 3 calibration: a stratified sample of Tier 2 and Tier 3 logged decisions is reviewed against expected outcomes. Community correction flags (users identifying incorrect collapses) feed a monthly calibration review. The metric that drives calibration is: fraction of clusters with only one effective independent source after collapse — both too-high and too-low values indicate miscalibration

*Clustering*

- Named entity extraction via spaCy `en_core_web_sm` (no Wikidata linking yet — entity names extracted as strings, full resolution deferred to Part B)  
- Cluster candidates identified by: entity overlap score \+ semantic similarity score \+ temporal proximity (72-hour window)  
- Combined score above threshold → assigned to existing cluster or seeds a new one  
- Cluster lifecycle: active (receiving new articles), dormant (no new articles for 48 hours), merged (absorbed into a larger related cluster)  
- Cluster metadata computed on assignment: total source count, independent source count (adjusted for outlet parent\_org\_name matching), geographic spread by country

*Categorisation*

- Ollama categorisation job runs in Celery, consuming from a queue populated at ingest  
- Model: Mistral 7B Instruct Q4\_K\_M — serves both categorisation and translation review tasks via sequential loading, avoiding RAM contention on the 16GB VPS  
- Prompt instructs model to classify article into one or more of the broad category taxonomy  
- Results stored as category\_id on the article record  
- In Phase 1, this runs locally via your MacBook Ollama instance; the Celery worker makes HTTP requests to `localhost:11434` in dev

*Pre-computation and caching*

- Celery beat scheduler runs pre-computation jobs on a rolling cycle  
- Digest pre-computation: for each active user preference profile, assembles the top story clusters per followed category, stores result in Redis with a 1-hour TTL  
- Cluster summary pre-computation: headline, source count, category, geographic spread, left/right political spread (from seeded outlet data), cached in Redis  
- Cache invalidation: cluster cache invalidated when a cluster receives a new member; digest cache invalidated on the hourly cycle

*OpenClaw integration*

- OpenClaw is a self-hosted messaging gateway that connects chat applications to AI agents via a custom AgentSkills system. It is not a pipeline orchestration layer — Celery handles all scheduled and background jobs. OpenClaw's role in this project is as a human-facing monitoring and control interface: custom skills (each a `SKILL.md` file) expose pipeline operations and system state to the developer via a preferred chat channel (Slack, Discord, Telegram, etc.)
- OpenClaw deployed on VPS alongside other services  
- Initial custom AgentSkills built during Phase 1:
  - **Ingest skill** — triggers a feed ingestion run on demand, returns article count and any source failures  
  - **Health skill** — queries Celery queue depth, Redis cache freshness, and database row counts; returns a status summary  
  - **Cluster skill** — returns clustering stats for the last 24 hours (clusters created, merged, dormant)  
  - **Source skill** — lists active sources, flags sources that have failed to fetch in the last cycle  
- Pipeline orchestration (scheduled ingestion, clustering passes, pre-computation) remains owned by Celery Beat throughout all phases; OpenClaw provides the developer-facing control surface above it

---

### Phase 2 — MVP Clients

**Goal:** A usable product. You read your morning news through it. The Flutter PWA runs on macOS. The CLI runs on Linux. Both are fully functional within MVP scope.

**Duration:** 7–10 weeks

**Learning investment this phase:** Flutter and Dart are the primary investment. This is the steepest learning curve in the whole project. The ambient learning from Phases 0 and 1 matters — do not skip it. By Phase 2, you should have enough Dart familiarity to build UI components without constant reference. Plan for the first 2–3 weeks of this phase to be slower than feels comfortable.

Flutter state management: Bloc (with Cubit for simpler screens) is the chosen approach. Bloc's strict separation of events, states, and business logic suits a project of this data complexity — multiple interconnected streams, deep state across views, cross-platform targets — and its explicitness will help when revisiting code after weeks away. Cubit reduces the boilerplate overhead on straightforward screens without abandoning the Bloc pattern.

**Deliverables:**

*Flutter Web PWA*

Onboarding flow (3 questions):

- Q1: What brings you here? (staying informed / research / professional use / all of the above)  
- Q2: What do you want to follow? (category multi-select from taxonomy, optional sub-niche text input)  
- Q3: How do you like to engage with news? (quick summaries / full stories with context / everything)  
- All three write to user\_preferences via the API; onboarding is skippable with sensible defaults  
- Desktop-first layout; mobile browser layout prepared for Phase 5 native conversion

Digest view:

- Personalised story clusters grouped by followed category  
- Each cluster card: headline (from most-cited title in cluster), source count, time since first published, category label, geographic spread indicator, left/right political spread bar (from seeded outlet data averaged across cluster sources)  
- Free tier: one representative article per cluster visible, selected by the **Representative Article Score (RAS)**; total source count displayed prominently  
- Pull-to-refresh triggers a cache refresh for the user's digest

**Representative Article Score (RAS):** A transparent, multi-dimensional score used to select the single article shown to free-tier users for each cluster. All dimensions, weights, and methodology are publicly documented and subject to the RFC process. Weights are stored in the database settings table alongside wire propagation thresholds. The full six-dimension score requires feature analysis data available from Phase 4; the MVP uses the two dimensions computable from Phase 1 data only (completeness and originality), with the remaining dimensions defaulting to 0.5 (neutral) until Phase 4 activates them:

| Dimension | MVP weight | Full weight | Source |
| :---- | :---- | :---- | :---- |
| Completeness | 0.50 | 0.15 | Fields present on article record |
| Originality | 0.50 | 0.25 | Wire propagation tier (already computed) |
| Outlet peer-normalised quality | — (0.5 default) | 0.20 | Feature analysis system (Phase 4+) |
| Political centroid proximity | — (0.5 default) | 0.20 | Outlet leaning vs. cluster median (Phase 4+) |
| Primary source density | — (0.5 default) | 0.15 | Named citations per 1,000 words (Phase 4+) |
| Temporal position | — (0.5 default) | 0.05 | Publication order within cluster, log-scaled |

The political centroid proximity dimension is the key anti-bias mechanism: it selects the article whose outlet sits closest to the political centre of gravity of all articles in the cluster, preventing systematic bias toward any part of the political spectrum in the default free-tier view. Phase 4 activates all six dimensions without any change to the user-facing interface.

Cluster view (tapping a digest card):

- List of all deduplicated sources (free tier) with outlet name, country flag, publication timestamp, left/right indicator for that outlet  
- Outlet card: tapping an outlet name shows a small inline card with outlet name, country, parent organisation (if known), political leaning (seeded), and a link to the original article  
- Source count total displayed with clear visual indication that paid tier unlocks full article list  
- Geographic spread: simple list of countries with article counts

User preferences:

- Category management (add/remove followed categories and sub-niches)  
- Digest time setting  
- Depth preference toggle (affects default view density)  
- Account settings (email, password change)

*Python CLI client*

- pip package installable via `pip install [project-name]` on any Linux system with Python 3.10+  
- Three-question onboarding via sequential terminal prompts; writes config to `~/.config/[project]/config.json`  
- `digest` command: text-formatted story clusters by followed category, outlet names, source counts  
- `cluster <id>` command: full source list for a cluster, outlet details, left/right indicator  
- `outlet <domain>` command: outlet profile card in text format  
- `search <query>` command: semantic search against article titles and summaries  
- `prefs` command: view and edit preferences  
- All commands hit the FastAPI backend; auth token stored in config file  
- Help text on every command: `[project] --help`, `[project] digest --help`  
- Full feature parity with the PWA within MVP scope — no exceptions

*User account system*

- Registration and login endpoints wired to Flutter and CLI clients  
- JWT tokens with refresh (7-day access token, 30-day refresh token)  
- Password reset via email via Resend; email service abstraction layer implemented from the start so provider can be swapped without rewriting call sites  
- Single tier at this stage: all users are on the free tier, no payment infrastructure yet

---

### Phase 3 — Hardening and Soft Launch

**Goal:** The product is stable enough to put in front of real people. You have been using it daily. Ten to twenty other people are using it. You are collecting feedback and finding out what matters most to them.

**Duration:** 4–5 weeks

**This phase is about proving the concept, not building features.** No new features are added in Phase 3\. The work is stability, quality, performance, and the infrastructure for going public in a controlled way.

**Deliverables:**

*Stability and quality*

- Wire propagation thresholds calibrated against the real corpus — tune both the similarity threshold and the time window based on observed false positives and false negatives  
- Celery job failure handling: dead letter queue, retry logic with backoff, failure alerting  
- API error handling: consistent error response format, no raw stack traces in production  
- Database query optimisation: identify slow queries with pg\_stat\_statements, add indexes where needed  
- Redis cache TTL tuning based on observed usage patterns  
- Rate limiting on all API endpoints (fastapi-limiter or equivalent)

*Source library expansion*

- OPML library expanded to 500+ sources, focused on category coverage gaps identified during self-use  
- GDELT connector validated against real data, edge cases handled  
- Feed health monitoring: sources that consistently fail to fetch are flagged for review

*Testing*

- Unit tests for all pipeline components: deduplication logic, clustering logic, categorisation, cache computation  
- Integration tests for all API endpoints against a test database  
- Data quality assertions run daily: no articles without source citations, no clusters with zero members, no outlet records missing required fields  
- Performance baseline: pre-computed layer response times measured and documented (target: \<100ms p95)

*Monitoring*

- Sentry error tracking deployed (free tier covers this phase)  
- Healthchecks.io monitoring for all Celery beat jobs  
- Basic uptime monitoring for the API  
- Structured JSON logging to file, log rotation configured

*Ollama on VPS*

- Ollama deployed to VPS alongside other services (requires CX41 or above for comfortable RAM headroom)  
- Categorisation jobs now run entirely on VPS; local MacBook Ollama no longer required for production

*Public infrastructure (minimal)*

- GitHub repository published with AGPL licence, README, and self-hosting documentation  
- Simple single-page landing site: what the project is, why it exists, sign up link  
- Privacy policy (basic, appropriate for a pre-commercial product with no payments — can use a standard open source project privacy policy template as a starting point)

*Soft launch*

- Invite 10–20 people: a mix of journalists, researchers, people interested in media criticism, and trusted technical users who can give useful feedback  
- Structured feedback collection: what works, what's confusing, what's missing, what would make them use this daily  
- Feedback informs the Part B feature prioritisation — what gets built first in Phase 4 is driven by what the soft launch group actually asks for

**Phase 3 triggers for moving to Part B:**

- The product has been in daily personal use for at least 4 weeks without major issues  
- At least 5 soft launch users are using it with some regularity and have provided feedback  
- The core clustering and outlet context features are demonstrably useful to real people

---

## Part B — Full Product Roadmap

Part B work does not begin until all three Phase 3 triggers are met. The feature priorities within Part B are informed by soft launch feedback and may differ from the order presented here.

---

### Phase 4 — Feature Layer 1

**Goal:** The product earns its first paying users. Stripe is live. The analytical depth that differentiates this platform from a simple RSS aggregator begins to emerge.

**Duration:** 10–14 weeks

**Deliverables:**

*Analytics depth*

- Translation pipeline: built in Phase 4 using **OPUS-MT** (Helsinki-NLP models, self-hosted via HuggingFace, zero per-character cost). On-demand translation only — translate when a user views a non-English article, cache the result permanently. Gated behind the paid tier from day one: every translation request is from a user generating revenue contribution. OPUS-MT quality is below DeepL for political and legal language but is sufficient to establish the pipeline, test the architecture, and deliver value to early paid users. DeepL is swapped in as the production engine in Phase 5 (see Phase 5) once revenue supports the cost. The swap is a config-level change, not a rebuild. LLM review pass for flagging, confidence annotation, and original language accessible alongside translation apply regardless of translation engine  
- Political leaning calculation from content (NLP, replacing seeded data): word embedding analysis, entity framing, comparative framing against corpus average, citation network signals. Seeded data remains as a fallback and calibration reference  
- Author profiles: independent of outlet, persisting across employer changes, seeded from byline data in the corpus  
- Full outlet feature analysis: all dimensions from CONCEPT.md Section 5 (textual independence score, correction record, original reporting ratio, vindication signal, contrarian vindication, primary source citation rate, peer-normalised consistency)  
- Basic influence graph: ownership relationships sourced from Wikipedia and Companies House (UK), manually curated for major outlet groups initially. Rendered using **Cytoscape.js** via Flutter's `HtmlElementView` — Cytoscape.js is battle-tested for network graphs at scale (thousands of nodes and edges), MIT licensed, and handles the filtering, layout algorithms, and interaction patterns the influence graph requires. For Phase 5 native builds, the same Cytoscape.js graph is wrapped in a `WebView` widget. This avoids a rewrite when graph complexity grows; do not use graphview or fl_chart for this feature  
- Coverage distribution analysis: per-cluster source counts by region and language, framing divergence initial implementation (three signals: sentiment differential per entity mention \+ topic emphasis differential \+ lexical divergence — displayed as a per-dimension breakdown, not collapsed into a single score), global distribution view  
- Contrarian vindication pipeline: two-stage system — Stage 1 statistical proxy (embedding divergence tracking at ingest, always-on) feeds candidates to Stage 2 LLM factual compatibility checking (top-N daily divergents checked against later cluster consensus via Mistral 7B, narrow factual brief). Both stages must pass (AND condition). N is adaptable: `N = max(5, min(50, daily_active_clusters × 0.5))`, stored in the database settings table alongside wire propagation thresholds. Phase 4 implementation flags candidates for human review; automated scoring introduced progressively in Phase 5

*Sources expanded*

- Social media connectors: Bluesky and Mastodon (institutional accounts only — manual curation against a documented checklist: named organisation or working journalist, minimum six months public posting history, primarily news-adjacent content; account categories: government, media organisation, journalist, NGO, corporation, official body; addition and removal process publicly documented). LinkedIn and X/Twitter deferred to Phase 5/6 — see Phase 5 notes  
- **LinkedIn API application initiated during Phase 4 (not blocking, but time-sensitive):** LinkedIn requires advance application to the LinkedIn Partner Program or Marketing Developer Platform before programmatic API access is granted. The process has no guaranteed approval timeline. To have LinkedIn available in Phase 5, the application must be submitted during Phase 4. Submit during Phase 4 development; do not wait until Phase 5 starts  
- NewsAPI.org connector added in this phase: commercial API terms now funded (~$449/month paid tier); ~150,000 source index adds meaningful breadth to Layer 1 coverage  
- Wikidata entity linking: spaCy's native `EntityLinker` with a custom `KnowledgeBase` implementation. Build process: (1) download a filtered Wikidata JSON dump scoped to entities with ≥20 sitelinks (covers all entities likely to appear in news coverage); (2) populate `InMemoryLookupKB` with Q-IDs, canonical names, descriptions, and alias sets from Wikidata label/alias data; (3) use sitelink count as prior probability for disambiguation — a strong signal in news contexts; (4) fine-tune the disambiguation model using Wikipedia anchor text as training data. The KB is refreshable from a new Wikidata dump without retraining the disambiguation model. No external API dependencies; runs fully self-hosted  
- Reddit API connector added (Hacker News already live from Phase 1)  
- Academic source connectors: arXiv, PubMed  
- **Whisper transcript generation** (Celery background job): for a curated list of high-value investigative journalism podcasts where no Podcasting 2.0 transcript is provided, Whisper (open source, self-hosted) generates transcripts from the original audio. Scoped narrowly — this is not applied to all podcasts, only a maintained list of sources where transcript value justifies the compute. Citation stored as: "Transcript generated from audio: [podcast name], [episode title], [date]; local speech recognition model." Third-party transcript services are not used

*Payments and tiers*

- Stripe integration: subscription creation, management, webhook handling for subscription events  
- Professional tier enforced: full article cluster access, all feature analysis dimensions, API access (read-only, rate limited), data export (JSON, CSV)  
- Free tier clearly delineated: deduplicated view, source counts, basic outlet info, left/right surface  
- Geographic pricing implemented (purchasing-power-adjusted bands — research required)  
- Upgrade prompts: data-driven, contextually placed, never aggressive. The data sells the upgrade

*Notifications (basic)*

- Email digest via Resend: daily digest to email for users who opt in, off by default  
- Personal updates feed: a dedicated browsable tab giving each user a condensed, interest-specific stream of story developments, entity appearances, and coverage changes in their followed topics. Always present in the app; updated continuously. Push notifications (introduced in Phase 5\) point users here; the feed provides the substance  
- Push notification threshold logic (ready for Phase 5 activation): Digest fires once at user's chosen time; Tracked topics fires when a followed cluster receives ≥5 new independent sources within 4 hours, or when a followed entity appears in a new cluster; Breaking fires on a coverage spike of ≥20 new independent sources on any single cluster within 2 hours. All thresholds stored in the database settings table, user-adjustable within system-defined ranges, all off by default

**Prerequisites for this phase:**

- UK Ltd company incorporated and bank account open before Stripe goes live — this must be actioned during Phases 0–2, not at the start of Phase 4  
- Specific tier pricing and geographic pricing bands determined through market research before Stripe launch  
- Commercial licence terms drafted (legal review)  
- Privacy policy updated for commercial product (legal review)  
- Google OAuth integration (via authlib): requires verified domain, legal entity, and an updated privacy policy to register an OAuth client — all of which are in place by Phase 4. Implemented as an additive convenience login option alongside email/password; not a dependency for any feature

---

### Phase 5 — Feature Layer 2 and Public Launch

**Goal:** All features from CONCEPT.md are built and working. Native apps are in the App Store and Google Play. The platform has a public launch. This is the complete product.

**Duration:** 10–14 weeks

**Deliverables:**

*Sources expanded*

- **Translation engine upgrade: OPUS-MT → DeepL API.** By Phase 5, Stripe is established and revenue is sufficient to absorb translation costs. DeepL API Pro ($5.49/month base + $25/1M characters) replaces OPUS-MT as the translation engine. The switch is a config-level change — the pipeline architecture is unchanged. Monitor cost per translated article against revenue contribution from Phase 5 launch; if the ratio is healthy, consider expanding translation access beyond the paid tier. If cost growth becomes a constraint, implement language filtering (only translate languages above a minimum corpus-volume threshold)
- **Translation trigger upgrade: on-demand → at-ingest (conditional).** Evaluate during Phase 5 whether framing divergence analysis across languages requires a pre-translated corpus. If so, enable background at-ingest translation for high-volume language groups; on-demand translation remains for lower-volume languages. DeepL at-ingest across all ingested content at full corpus scale is expensive — this decision is made on evidence from Phase 5 usage patterns, not in advance
- **LinkedIn (institutional accounts only):** API access available if the Phase 4 Partner Program application was approved. Covers corporate and institutional announcements. Same curation checklist applies. If the application is still pending, LinkedIn is deferred to Phase 6  
- **X/Twitter (institutional accounts only):** API access evaluated and introduced if commercially justified at this phase. Cost assessment required before implementation — X/Twitter's API pricing has increased significantly and varies by access tier. The same curation checklist applies (named organisation or working journalist, minimum six months posting history, primarily news-adjacent content). If API cost is prohibitive, X/Twitter remains deprioritised to Phase 6 or excluded

*Remaining visualisations and analytical features*

- Story provenance visualisation: directed graph showing information genealogy from origin to cluster  
- Narrative evolution timeline: chronological view of how facts, sources, framing, and volume changed over a story's life  
- Full entity tracking: entity profile pages, entity knowledge graph (navigable relationship graph), historical depth  
- Stakeholder analysis: per-cluster documented entities with stakes, stake types, source citations, financial relationships with covering outlets  
- Multi-axis political leaning: economic, social, and institutional axes beneath the left/right surface; cultural contextualisation per region  
- Global coverage map: geographic heat map with framing divergence indicators  
- Full influence graph: all edge types, full filtering (ownership, citation, funding, editorial partnership), saved filter states  
- Corporate ownership tree: navigable from any outlet or entity node

*Sub-niche system*

- Default sub-niche taxonomy: curated defaults per broad category (e.g. "AI regulation" under Technology, "climate policy" under Environment, "monetary policy" under Business) — taxonomy designed during Phase 4 using soft launch feedback  
- User-definable sub-niches via free text, matched against the article corpus via semantic similarity; cross-category following supported (e.g. "AI regulation" spanning Technology and Politics)  
- Entity-graph-following as a niche discovery mechanism (following an entity automatically surfaces related coverage) introduced in this phase

*Notifications complete*

- Push notifications: iOS, Android, macOS, Windows  
- SMS alerts via Twilio: opt-in, recommended for breaking events only, off by default  
- All notification levels configurable; all off by default; no dark patterns

*Native app builds*

- Flutter → native iOS: platform UX polish, gesture navigation, iOS notification integration  
- Flutter → native Android: Material 3 polish, Android notification integration  
- Flutter → native macOS: menu bar integration, keyboard navigation  
- Flutter → native Windows: Windows notification integration, signed installer  
- App Store submission: Apple review compliance, privacy policy, metadata  
- Google Play submission: review compliance, metadata  
- macOS independent distribution: signed and notarised DMG  
- Windows independent distribution: signed installer

*Academic/NGO tier*

- Research-appropriate data export formats  
- Extended historical data access  
- Citation-ready provenance documentation  
- Adjusted pricing for non-commercial research use

*Public launch infrastructure*

- Full methodology documentation site: transparent account of every calculation, publicly readable  
- RFC process infrastructure: public repository for methodology change proposals  
- Community feedback and factual error flagging system  
- Public changelog

*AGPL and licensing*

- Commercial licence terms published (for non-AGPL deployment)  
- Contributor guidelines if community contribution is invited

**Prerequisites for this phase:**

- App Store and Google Play developer accounts registered  
- Apple notarisation and signing certificates obtained  
- Commercial licence terms published (legal review)  
- Marketing site designed and ready for launch

---

### Phase 6 — Enterprise and Scale

**Goal:** Institutional users. Scaled infrastructure. Enterprise sales motion operational.

**Duration:** Ongoing

**Go-to-market approach:** Inbound-first. The methodology documentation site and RFC process are themselves inbound assets — institutional users who scrutinise the methodology are already self-qualifying. Academic publishing (working papers, journalism and media studies conference presence) establishes credibility without a sales team. Direct outbound outreach to target institutions begins once inbound demand provides a case study base. Partnership with enterprise software vendors is a later consideration once independent market presence is established.

**Deliverables:**

*Enterprise API*

- GraphQL endpoint for complex relational queries  
- API key management with permission scopes  
- Tiered rate limiting and data volume limits per tier  
- Webhook system: registered endpoints, payload schemas, retry logic, delivery guarantees  
- JSON-LD and RDF export formats  
- Versioned API with documented deprecation process  
- Sandbox environment with fixed sample dataset  
- Full public API documentation

*Enterprise product*

- Custom dashboards: entity-set or topic-domain scoped, configurable layout  
- Real-time monitoring: entity and topic threshold alerting  
- White-labelling options  
- Bulk export pipelines  
- SLA infrastructure and monitoring  
- Dedicated enterprise support channel and onboarding process  
- Enterprise contract template

*Infrastructure*

- Kubernetes orchestration replacing Docker Compose  
- Horizontal scaling per service layer  
- PostgreSQL read replicas  
- ClickHouse data warehouse for analytical query separation  
- CDN for static assets  
- Load balancer for API layer  
- Enterprise-grade backup and recovery

**Prerequisites for this phase:**

- SLA tier definitions and commitments agreed  
- White-labelling scope and technical implementation designed  
- Data warehouse migration strategy from PostgreSQL analytical queries to ClickHouse planned

---

## 5\. Infrastructure and Operations

### VPS — Hetzner CX41

4 vCPU, 16GB RAM, 160GB SSD, \~£13/month. Helsinki or Falkenstein data centre (European data residency, GDPR-aligned). The 16GB RAM supports PostgreSQL, Redis, Celery workers, and Scrapy/Playwright simultaneously. Ollama model serving (Mistral 7B Instruct Q4\_K\_M, \~8GB RAM) is the most memory-intensive component and is handled via sequential loading. **RAM headroom is tight under real ingestion load**: while categorisation is running, PostgreSQL (2–4GB), Redis and Celery workers (2–3GB), and the Ollama model together approach the 16GB ceiling. Test this ceiling during Phase 1 development. If memory pressure is observed, the upgrade path is the Hetzner CX51 (32GB RAM, \~£26/month) — same architecture, same data, no migration required beyond a resize. Storage will grow significantly as the corpus expands; additional Hetzner volumes can be attached without migration.

### Backup strategy

The backup approach is phased to match storage volumes and tooling requirements at each stage. Proton Drive (500GB, already available) is used as the primary off-site backup destination in the early phases. Hetzner Object Storage (S3-compatible) is introduced when continuous WAL archiving becomes necessary and when backup volumes outgrow Proton Drive's capacity.

**Phases 0–2 — Proton Drive, daily dumps only**

Daily automated pg\_dump, compressed and transferred off-VPS via rclone to Proton Drive. Rolling 30-day retention. Backup volumes at this stage are well under 100GB — comfortably within the 500GB available. Continuous WAL archiving is not set up in these phases; daily dumps are sufficient for a pre-launch system with no paying users. Worst-case data loss exposure: up to 24 hours. Restore procedures documented and tested before Phase 2 goes live.

Redis: append-only file (AOF) persistence for the job queue. Pre-computed cache data is reconstructable from PostgreSQL and does not require backup.

**Phase 3 — Proton Drive for dumps, Hetzner Object Storage for WAL**

Soft launch puts real users on the platform. The 24-hour data loss tolerance becomes less acceptable. A small Hetzner Object Storage bucket is added solely for continuous WAL archiving, providing point-in-time recovery without replacing Proton Drive for daily dumps. At Phase 3 WAL volumes (\~200–500MB/day compressed), the Hetzner cost is under €1/month. Proton Drive continues to hold daily dumps; backup volumes by end of Phase 3 are estimated at 100–170GB.

**Phase 4 — transition to Hetzner Object Storage as primary**

Translation storage, entity data, and expanded source coverage push backup volumes toward and potentially beyond Proton Drive's 500GB ceiling during Phase 4\. At this point Hetzner Object Storage becomes the primary backup destination for both daily dumps and WAL archiving — the S3-compatible tooling (WAL-G or pgbackrest) integrates natively, and the cost at this scale (\~€12–25/month for 500GB–1TB) is justified. Proton Drive is retained as a secondary cold store for monthly snapshots, providing a second off-site copy at no additional cost.

Tiered retention is introduced here: daily dumps kept for 7 days, weekly snapshots kept for 4 weeks. This roughly halves storage consumption compared to flat 30-day daily retention with minimal practical loss of recovery granularity.

**Phase 5+ — tiered retention, review pgvector backup scope**

As database size grows into the 150–400GB range, evaluate whether pgvector indexes need to be included in daily dumps. The HNSW index adds \~1.5–2× the raw vector storage to backup size; since indexes can be regenerated from the stored embedding data, excluding them from daily dumps and including them only in weekly snapshots is a reasonable trade-off at this scale.

Redis: AOF persistence for the job queue throughout all phases. Cache data remains reconstructable from PostgreSQL and does not require backup at any phase.

### Security baseline (Phase 0\)

- SSH key authentication only; password authentication disabled  
- Firewall: only ports 22 (SSH), 80 (HTTP redirect), 443 (HTTPS) open externally  
- API authentication enforced on all non-public endpoints  
- Secrets managed via environment variables, not committed to version control  
- Dependency vulnerability scanning in CI/CD pipeline  
- Regular security updates automated

### Monitoring and alerting

**Phases 0–5:** Sentry for error tracking and exception monitoring (free tier sufficient through soft launch). Healthchecks.io for Celery beat job monitoring. Structured JSON logging to file with log rotation. **Phase 6:** Grafana \+ Prometheus \+ Loki stack introduced when enterprise operational complexity justifies the additional infrastructure.

Coverage across all phases: API response time and error rates, database query performance, Celery queue depth and job failure rates, ingestion pipeline health (articles ingested per hour, source failures), disk and memory usage. Alerting reaches the developer without requiring a separate monitoring service to be operational.

---

## 6\. Testing Strategy

Testing approach is defined at a principle level. Specific tooling and coverage requirements are Phase 0 deliverables.

**Unit tests** — all pipeline processing functions: deduplication logic, clustering logic, entity resolution, feature analysis computation, political leaning calculation, translation confidence scoring. Coverage target: 80% minimum on pipeline components.

**Integration tests** — API endpoints against a test database with seed data. All ingestion connectors tested against fixture responses (not live APIs). Stripe webhook handling.

**End-to-end tests** — Flutter: user flows through onboarding, digest view, cluster view, feature analysis fingerprint. CLI: equivalent flows in terminal. Triggered on main branch push.

**Data quality tests** — automated assertions on ingested data: no articles without source citations, no entity links without confidence scores, no stakeholder entries without documented sources. Run daily against the live database.

**Performance tests** — pre-computed layer response time (target: \<100ms p95 for digest and cluster summary responses). Analytical layer response time (target: \<5s p95 for standard research queries). Load tests before public launch.

**Tooling:** Python backend — pytest \+ pytest-asyncio \+ httpx \+ factory-boy. Flutter — built-in Flutter test framework \+ integration\_test package for end-to-end flows. Coverage target: 80% minimum on all pipeline processing components.

---

## 7\. Risk Register

| \# | Risk | Likelihood | Impact | Mitigation |
| :---- | :---- | :---- | :---- | :---- |
| R1 | Source API rate limits or terms of service changes block a significant collection layer | Medium | High | Diversify across many source layers; monitor terms changes; design ingestion layer to be source-agnostic so alternatives can be substituted |
| R2 | Ollama LLM inference too slow on VPS hardware for real-time categorisation | Medium | Medium | Pre-computation model; batch categorisation rather than real-time; upgrade VPS RAM if needed; route to cloud API as fallback |
| R3 | DeepL API costs exceed revenue at introduction | Low (Phase 4) / Medium (Phase 5+) | Medium | DeepL deferred to Phase 5 until revenue is established; OPUS-MT (free, self-hosted) used in Phase 4. When DeepL is introduced: on-demand with permanent caching, gated behind paid tier, language volume filtering if cost growth outpaces revenue |
| R4 | Political leaning calculation generates controversy from outlets objecting to their assigned position | Medium | High | Full methodology transparency; RFC process for challenges; conservative initial rollout; clear legal framing as descriptive not judgmental |
| R5 | Entity resolution produces systematic errors for less-prominent entities | High | Medium | Conservative confidence scoring; community correction queue; surface uncertainty to users rather than hiding it; prioritise prominent entities in initial implementation |
| R6 | App Store rejection of iOS/macOS build (Phase 5\) | Low | High | Review Apple guidelines during Phase 4 design; avoid features that trigger common rejection reasons; allow buffer time in Phase 5 timeline |
| R7 | GDPR compliance issues in EU user data handling | Medium | High | Data minimisation by design; privacy policy review before Phase 4; user data stored only as required; no advertising use of data; legal review of data residency |
| R8 | Wire propagation thresholds incorrectly collapse genuine independent reporting | Medium | Medium | Start conservative; calibrate empirically; make thresholds configurable; surface the underlying data so users can identify issues |
| R9 | Coordinated bad-faith use of the community feedback system to game feature analysis | Medium | Medium | Strict scope limitation on what feedback can affect; RFC process gates methodology changes; full public audit trail of all accepted changes |
| R10 | Single-developer bus factor | High (if solo) | High | Document architecture and decisions thoroughly; AGPL licence ensures continuity even if project is abandoned; consider inviting contributors from Phase 4 |
| R11 | Storage cost growth outpaces revenue during corpus expansion | Medium | Medium | Storage budgeting from Phase 1; article body compression; archival policy for old content; historical depth gated behind paid tiers |
| R12 | Social media platform API access restricted or priced out of reach | Medium | Medium | Social layer is supplementary not primary; design ingestion so it degrades gracefully if a platform's API becomes unavailable |

---

## 8\. What Remains to Action

The following items are the remaining agenda before Phase 0 can begin. Some are technical decisions; others are real-world actions with lead times that run in parallel with development.

**Before Phase 0 begins — technical (blocking):**

- Phase 0 deliverables as specified in Section 4 (infrastructure, schema, API skeleton, dev tooling)

**Before Phase 0 begins — real-world (parallel track, not blocking early development):**

- Legal entity formation (\#15): UK Ltd incorporation, bank account, accountant engagement. Start immediately — lead time is weeks and it must complete before Stripe goes live in Phase 4\. This runs in parallel with Phase 0–2 development, not after it

**Phase 4 decisions (required before Stripe and public-facing launch):**

- Specific tier pricing and geographic pricing bands (requires market research at that point)  
- Commercial licence terms (legal review)  
- Privacy policy and terms of service (legal review, must cover commercial product)  
- Marketing site design and content

**Phase 5 decisions (required before native app submission):**

- App Store and Google Play developer account setup  
- Apple notarisation and signing certificates  
- Sub-niche default taxonomy design (informed by soft launch feedback — \#11)

**Phase 6 decisions (required before enterprise sales motion begins):**

- Enterprise go-to-market refinement beyond the confirmed inbound-first strategy (\#16)  
- SLA tier definitions and commitments  
- White-labelling scope and technical implementation  
- Data warehouse migration strategy (PostgreSQL → ClickHouse)

---

*End of Project Document v0.4* *Status: Approved for development — v0.4* *Reference: CONCEPT.md v0.4*  
