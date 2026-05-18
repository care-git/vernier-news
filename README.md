# Vernier News

Global media intelligence platform. Maps the terrain of news reporting — who covers stories, from what political position, with what ownership relationships, and with what distribution.

## Quick start

```bash
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD and JWT_SECRET_KEY at minimum

make up       # start all services
make migrate  # apply schema
make seed     # load initial outlets and categories
```

API docs available at `http://localhost:8000/docs` once running.

## Development

```bash
pip install -e ".[dev]"
make test     # run test suite
make lint     # ruff + black check
make format   # auto-fix formatting
```

## Common tasks

```
make up           start services (detached)
make down         stop services
make migrate      apply pending migrations
make migration name="describe change"   generate new migration
make seed         load seed data
make logs         tail API logs
make shell        bash into API container
```

## Licence

AGPL-3.0-or-later. See [LICENSE](LICENSE).
Commercial licensing available — contact billy@jecks.co.uk.

