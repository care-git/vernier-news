# Spec — Vernier Telegram Control Bot

*Status: approved for build — v1*

Replaces the LLM-driven OpenClaw gateway with a deterministic Python Telegram bot
that maps slash commands to the existing `/api/v1/admin/*` endpoints. Same channel
(Telegram), same operations, **no per-message LLM cost**.

## Background

The four OpenClaw skills (`vernier-health`, `vernier-ingest`, `vernier-clusters`,
`vernier-sources`) are each a single `curl` to an admin endpoint. The LLM (Haiku)
contributed no functional capability — it only parsed intent from natural language
and narrated the JSON back — but ran a full agent loop on every message, which is
what drove the credit spend. For four fixed operations, slash commands are cheaper
and faster.

## Scope

**In scope (v1):**

- Four on-demand commands mapping to the existing admin endpoints.
- Access restricted to an allowlist of Telegram user IDs (fail-closed).
- Proactive alerting: a daily health digest **and** threshold alerts
  (queue-depth spike, ingestion stall, API unreachable) with de-duplication.

**Non-goals:**

- Any natural-language understanding. Commands only.
- Direct DB/Redis access — the bot talks only to the HTTP admin API, reusing tested
  logic and keeping DB credentials out of the bot.

## Architecture

- **New `bot` service in `docker-compose.yml`**, gated behind a `bot` compose
  profile so it only starts where `COMPOSE_PROFILES=bot` is set (the VPS). Local dev
  that doesn't set the bot env vars never starts it. `restart: unless-stopped`.
- **Long-polling** (`getUpdates`) — only outbound calls to `api.telegram.org`. No
  inbound ports, nothing added to the attack surface, no webhook secret. Consistent
  with the "never expose extra ports" rule in HANDOFF.
- Reaches the API over the internal Docker network as `http://api:8000`, sending the
  `X-Admin-Key` header — exactly what the OpenClaw `run.sh` scripts did.
- Its own minimal `bot/Dockerfile` (`python:3.12-slim` + `python-telegram-bot`,
  `pydantic-settings`, `httpx`). It must **not** reuse the main image, which
  pre-downloads MiniLM + spaCy.

## Commands

| Command    | Endpoint                     | Notes                                   |
|------------|------------------------------|-----------------------------------------|
| `/health`  | `GET /admin/health`          | DB counts, Redis cache stats, queue depth |
| `/ingest`  | `POST /admin/ingest`         | Queues `ingest_feeds`; returns task id   |
| `/clusters`| `GET /admin/clusters/stats`  | Created / updated / dormant over 24h     |
| `/sources` | `GET /admin/sources`         | Outlet totals; lists inactive domains    |
| `/help`    | —                            | Lists commands                           |
| `/start`   | —                            | Greeting + command list                  |

**BotFather `/setcommands`:**

```
health - Pipeline health: DB, cache, queue
ingest - Trigger an immediate feed ingest
clusters - Cluster activity, last 24h
sources - Outlet / source summary
help - Show available commands
```

## Configuration (all via `.env`)

| Var | Purpose |
|-----|---------|
| `COMPOSE_PROFILES=bot` | Enables the bot service (set on the VPS) |
| `TELEGRAM_BOT_TOKEN` | From BotFather |
| `TELEGRAM_ALLOWED_USER_IDS` | Comma-separated Telegram user-id allowlist |
| `TELEGRAM_ALERT_CHAT_ID` | Chat that receives the daily digest + alerts |
| `ADMIN_API_KEY` | **Already present** — reused for `X-Admin-Key` |
| `BOT_API_BASE_URL` | Default `http://api:8000` (Docker network) |
| `BOT_DIGEST_UTC_HOUR` | Daily digest hour, default `8` |
| `BOT_ALERT_POLL_MINUTES` | Threshold poll interval, default `15` |
| `BOT_QUEUE_DEPTH_THRESHOLD` | Queue-depth alert threshold, default `100` |
| `BOT_INGEST_STALL_HOURS` | Hours without new articles before a stall alert, default `3` |

## Access control (mandatory)

Every command handler is wrapped with a `filters.User` allowlist; messages from
anyone else are silently ignored (no reply, so the bot's existence isn't confirmed).
If the allowlist is empty at startup, the bot **refuses to start** — fail closed,
mirroring the admin-key guard in `app/routers/admin.py`.

## Proactive alerting

- **Daily digest:** `JobQueue.run_daily` at `BOT_DIGEST_UTC_HOUR`, pushing the
  `/health` summary to `TELEGRAM_ALERT_CHAT_ID`.
- **Threshold poll:** `JobQueue.run_repeating` every `BOT_ALERT_POLL_MINUTES`, which
  checks `/admin/health` and alerts (once, with de-duplication) on:
  - **API unreachable** — the health call fails.
  - **Queue depth** — `celery_queue_depth` exceeds `BOT_QUEUE_DEPTH_THRESHOLD`.
  - **Ingestion stall** — the article count hasn't advanced for
    `BOT_INGEST_STALL_HOURS`.
  Each condition fires one alert on entry and one recovery message on exit; it does
  not re-alert every poll. All alerting is skipped if `TELEGRAM_ALERT_CHAT_ID` is
  unset.

## Error handling

- Admin client uses a 10s httpx timeout; every call is wrapped.
  - `403` → `⚠️ Admin key rejected`
  - connection error / timeout → `⚠️ API unreachable`
  - other non-2xx → `⚠️ API error {status}`
- A global PTB error handler logs exceptions so a bad update never crashes the bot.

## Repo layout

```
bot/
  __init__.py
  Dockerfile          # minimal python:3.12-slim image
  main.py             # build Application, register handlers + jobs, run_polling()
  config.py           # env → BotConfig (pydantic-settings)
  admin_client.py     # async httpx wrapper for the 4 admin endpoints
  handlers.py         # command handlers + global error handler
  alerts.py           # daily digest + threshold alert jobs
  formatting.py       # JSON dict → Telegram HTML
  auth.py             # allowlist filter
tests/bot/            # unit tests (formatting, admin_client, config — no telegram import)
```

## Testing

- Unit: `formatting` (JSON → expected HTML), `admin_client` (mocked httpx transport,
  including 403 and connection-error paths), `config` (allowlist CSV parsing). These
  avoid importing `telegram` so they run in CI, which installs `.[dev]` only.
- Manual acceptance: each command from an allowed account; silence from a
  non-allowed account; stop the `api` container and confirm `/health` returns
  `⚠️ API unreachable`.

## Rollout & decommission

1. Create the bot with BotFather; capture token; set the command list.
2. Add the env vars to the VPS `.env` (including `COMPOSE_PROFILES=bot`) and mirror
   placeholders into `.env.example`.
3. Land the `bot/` code, the `bot` compose service, and the `pyproject` extra.
4. `make build && make up` on the VPS → the bot container starts.
5. Verify allowed/denied behaviour and all four commands live.
6. `systemctl --user stop openclaw-gateway && systemctl --user disable openclaw-gateway`;
   remove the OpenClaw install if desired.
7. Keep `openclaw/skills/` in the repo as a record of the endpoint contract.

## Cost

~£0 ongoing: Telegram's Bot API is free; the container is ~40MB RAM; no LLM tokens.

## Future (Phase 3)

If conversational control is ever missed once Ollama is on the VPS, the same four
operations can be fronted by local inference at zero marginal cost. Not expected to
be necessary.
