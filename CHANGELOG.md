# CHANGELOG


## v0.1.0 (2026-05-19)

### Bug Fixes

- Celery Beat scheduling, Redis caching, pre-computation pipeline
  ([`3b31360`](https://github.com/care-git/vernier-news/commit/3b313604dc26724fd1aa6c132c0da382ff9b1588))

- Embeddings and wire propagation deduplication pipeline
  ([`e1db417`](https://github.com/care-git/vernier-news/commit/e1db417c88539894debc20665c4b6cc45fba89e4))

- Implement RSS ingestion and normalisation pipeline
  ([`65e90db`](https://github.com/care-git/vernier-news/commit/65e90db9ab42dcd868466e7e5c19551ff2a72282))

- Ollama categorisation pipeline
  ([`65074a5`](https://github.com/care-git/vernier-news/commit/65074a5e2c312fe93ce02d2089a43950ad263452))

- Resolve all CI lint failures (ruff + black)
  ([`1d303be`](https://github.com/care-git/vernier-news/commit/1d303be18a5b94c798f10fc6836e69798d7a2758))

- Run alembic and seed via docker compose exec
  ([`46704bf`](https://github.com/care-git/vernier-news/commit/46704bf2bb016cf81cfd059cb340505eaf9257c4))

- Spacy NER clustering pipeline with entity cache
  ([`c7ee308`](https://github.com/care-git/vernier-news/commit/c7ee308e4d5b0a92f7987109a11f9e8cfed08c8a))

- Use NullPool to resolve asyncio loop conflict in Celery tasks
  ([`74bc9dc`](https://github.com/care-git/vernier-news/commit/74bc9dcf8001730bebf58ddc7ceb45857bd14a8b))

- Widen collection_source to Text, NullPool for Celery async compat
  ([`27f688d`](https://github.com/care-git/vernier-news/commit/27f688de02ca71d096f6289e84df6878335d70b6))

- **ci**: Pass build_command as string to satisfy semantic-release v9 validation
  ([`9b3f55d`](https://github.com/care-git/vernier-news/commit/9b3f55d9b500d63b4c49a419bc9050582616dfd5))

- **ci**: Set build_command to empty string to skip PSR build step
  ([`d418cb9`](https://github.com/care-git/vernier-news/commit/d418cb98351c033724787dcc930a05391acf575c))

- **tests**: Use NullPool + sync setup_db to fix cross-event-loop errors
  ([`2d77b6b`](https://github.com/care-git/vernier-news/commit/2d77b6bb49f2c35d689467841ba1c7ab73b1cdbe))

### Build System

- Foundation commit
  ([`77c6d16`](https://github.com/care-git/vernier-news/commit/77c6d1675a6e1cf046b9c026f6837463237c036c))

- Openclaw integration
  ([`eed2b6c`](https://github.com/care-git/vernier-news/commit/eed2b6cd4a4ec051e2cc722356e5957e95114979))

### Features

- Api connectors - Guardian, GNews, Currents, NYT, GDELT, Hacker News
  ([`d095c12`](https://github.com/care-git/vernier-news/commit/d095c12f701eac14d3befb95f3c3c1c432d6c57a))

- Openclaw integration, admin endpoints
  ([`90d132a`](https://github.com/care-git/vernier-news/commit/90d132a71e2a915c2ab46cacd585c39ea51212f8))

- Pipeline skeleton and automated versioning
  ([`00b3f2f`](https://github.com/care-git/vernier-news/commit/00b3f2faff4f1763d101df6f5cc05d88fb54bb76))
