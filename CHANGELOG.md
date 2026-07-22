# CHANGELOG


## v0.13.0 (2026-07-22)

### Build System

- **bot**: Add telegram bot image and dependency
  ([`c60900a`](https://github.com/care-git/vernier-news/commit/c60900ae7b1bf448aa77720c002dc0cdb6fa3f35))

### Documentation

- Update HANDOFF.md to Phase 2 mid-point state
  ([`e46947e`](https://github.com/care-git/vernier-news/commit/e46947e1af9b51dfe045eb284fe60e8b5e259fbb))

Reflects completed auth, onboarding, and digest view features. Updates file tree, VPS status, CI
  version, local dev instructions (VPS-first workflow, port 8080), and remaining work list.

- **bot**: Document telegram bot config and spec
  ([`e41c046`](https://github.com/care-git/vernier-news/commit/e41c046e88f1312b149398f0141a144568d5390c))

### Features

- **bot**: Add bot service behind compose profile
  ([`4aedab7`](https://github.com/care-git/vernier-news/commit/4aedab7a639a758c465db534c7c908b27450f409))

- **bot**: Add telegram control bot with commands and alerting
  ([`dafb2e4`](https://github.com/care-git/vernier-news/commit/dafb2e4b4287faaf6d888eccc43f9e0aba558154))


## v0.12.3 (2026-07-20)

### Bug Fixes

- **client**: Redirect to digest after onboarding completes
  ([`2ce3112`](https://github.com/care-git/vernier-news/commit/2ce3112338759bf25d5b582d0e61d8b5e048c09f))

The redirect guard returned null when an established user (isNewUser: false) was still on
  /onboarding, leaving them stuck. Now any authenticated non-new-user on the onboarding route is
  sent to digest.


## v0.12.2 (2026-07-17)

### Bug Fixes

- **client**: Redirect to digest after onboarding completes
  ([`e2c7b6d`](https://github.com/care-git/vernier-news/commit/e2c7b6d5dd9cd9c524c5e265cab3598d366aee72))

The redirect guard returned null when an established user (isNewUser: false) was still on
  /onboarding, leaving them stuck. Now any authenticated non-new-user on the onboarding route is
  sent to digest.


## v0.12.1 (2026-07-17)

### Bug Fixes

- **client**: Redirect to digest after onboarding completes
  ([`f8c9229`](https://github.com/care-git/vernier-news/commit/f8c9229062f3768f2d02dc00c5d34a67b372cb02))

The redirect guard returned null when an established user (isNewUser: false) was still on
  /onboarding, leaving them stuck. Now any authenticated non-new-user on the onboarding route is
  sent to digest.


## v0.12.0 (2026-07-17)

### Features

- **client**: Add digest repository and cubit
  ([`df4bd81`](https://github.com/care-git/vernier-news/commit/df4bd81595cc37fdb268e44658fd07e1357aa279))

DigestRepository fetches GET /digest/. DigestCubit has load() for initial fetch and refresh() for
  pull-to-refresh, with DigestInitial, DigestLoading, DigestLoaded, DigestEmpty and DigestError
  states.

- **client**: Add digest screen and cluster card
  ([`52b9137`](https://github.com/care-git/vernier-news/commit/52b9137965b09e97416bfa3a744ea60029affb8b))

Category-grouped list with pull-to-refresh, empty and error states. ClusterCard shows headline,
  source counts, relative age, political spread bar and countries. Also wires onboarding and digest
  routes that were missing BlocProvider.value in the router.


## v0.11.0 (2026-05-22)

### Features

- **client**: Add three-step onboarding screen
  ([`26ee5b8`](https://github.com/care-git/vernier-news/commit/26ee5b8cd77fbc78a4b2c7305f7c08c004ec55d1))

PageView flow: purpose selection, category multi-select (pre-seeded from purpose choice), and depth
  preference. Animated selection cards and FilterChips. Skip saves defaults. OnboardingCubit scoped
  to the route via BlocProvider.value.


## v0.10.0 (2026-05-22)

### Features

- **client**: Add preferences repository and onboarding cubit
  ([`3c29760`](https://github.com/care-git/vernier-news/commit/3c2976069f6788423767ef6fed00d6dad807bd31))

ApiClient gains a put() method. PreferencesRepository wraps PUT /users/preferences. OnboardingCubit
  manages submit/skip and calls AuthCubit.completeOnboarding() on success to trigger the router
  redirect.


## v0.9.0 (2026-05-22)

### Features

- **client**: Add preferences repository and onboarding cubit
  ([`637736f`](https://github.com/care-git/vernier-news/commit/637736f497184cf43545049ba69fd0180aeafb7e))

ApiClient gains a put() method. PreferencesRepository wraps PUT /users/preferences. OnboardingCubit
  manages submit/skip and calls AuthCubit.completeOnboarding() on success to trigger the router
  redirect.


## v0.8.0 (2026-05-22)

### Features

- **api**: Add user preferences endpoint
  ([`407272a`](https://github.com/care-git/vernier-news/commit/407272a3e7b97fd04a7c2b311095bb870af93f0a))

PUT /users/preferences upserts a UserPreferences row for the authenticated user, storing purpose,
  category interests and depth preference. Returns the saved values.


## v0.7.0 (2026-05-22)

### Features

- **client**: Add auth redirect guard to router
  ([`29e5a2b`](https://github.com/care-git/vernier-news/commit/29e5a2be307f322a2fa151c29e3ce3cd80430083))

AppRouter uses GoRouterRefreshStream on the AuthCubit stream so redirects re-evaluate on every state
  change. Unauthenticated users are sent to /login; new registrations to /onboarding; authenticated
  users on auth routes to /digest. VernierApp is now a StatefulWidget that calls checkAuth() once in
  initState via BlocProvider.value.


## v0.6.0 (2026-05-22)

### Features

- **client**: Add login and register screens
  ([`d6abd2a`](https://github.com/care-git/vernier-news/commit/d6abd2ab99390658afa99a0d9911ae76f8fdbeaa))

Email/password forms with validation, password visibility toggle, confirm-password field on
  register, error banner from AuthCubit state, and loading state on the submit button.


## v0.5.0 (2026-05-22)

### Documentation

- Update to current development stage
  ([`fce669f`](https://github.com/care-git/vernier-news/commit/fce669f5709718004a9ff7569a3693b9b474b8cc))

### Features

- **client**: Add auth repository and cubit
  ([`c3e6f56`](https://github.com/care-git/vernier-news/commit/c3e6f56b58c171976362af86c2eea14d58d18a85))

AuthRepository handles login/register/getCurrentUser and token persistence. AuthCubit owns the
  AuthState sealed class with checkAuth/login/register/logout/completeOnboarding methods.
  GoRouterRefreshStream adapts the cubit stream for go_router.


## v0.4.0 (2026-05-20)

### Bug Fixes

- **api**: Format clusters router for Black
  ([`3c86955`](https://github.com/care-git/vernier-news/commit/3c8695513fc148ce2bdabb79c210eb56e75a67fa))

### Features

- **api**: Add API client and data models
  ([`2b2eb9d`](https://github.com/care-git/vernier-news/commit/2b2eb9dd8d65d94495316dc0527893080b788e06))

- **api**: Add response schemas, implement digest endpoint, configurable CORS
  ([`2a1e6bf`](https://github.com/care-git/vernier-news/commit/2a1e6bfd7f14ebb10375169a974aca1272707edc))


## v0.3.0 (2026-05-20)

### Chores

- **infra**: Move api hot-reload into docker-compose.override.yml
  ([`6ef4e0c`](https://github.com/care-git/vernier-news/commit/6ef4e0c21b8ffbba58f978450e4a1fc8b9ec894b))

### Documentation

- Update to reflect pre-Phase 2 infrastructure hardening
  ([`e6f138a`](https://github.com/care-git/vernier-news/commit/e6f138ad9e0b6a0b3e12201bb6ef6626a8a95a51))

### Features

- **client**: Scaffold Flutter web project with routing, theme, and DI
  ([`5dcea33`](https://github.com/care-git/vernier-news/commit/5dcea33ebadc8ecedbfba42dd4628dabd4eb464f))


## v0.2.0 (2026-05-20)

### Features

- **infra**: Add Caddy reverse proxy with auto-TLS and tighten CORS to vernier.news
  ([`f14fd08`](https://github.com/care-git/vernier-news/commit/f14fd08d910fba552f2d11831ba30dfc0892051e))


## v0.1.2 (2026-05-20)

### Bug Fixes

- **infra**: Remove public port bindings for Redis and PostgreSQL, bind API to loopback
  ([`e6c01d7`](https://github.com/care-git/vernier-news/commit/e6c01d78696da43e5f405abb4c63ed8f73aa4442))


## v0.1.1 (2026-05-19)

### Bug Fixes

- **routers**: Use .is_(None/True) for correct SQL NULL and boolean comparisons
  ([`de507a9`](https://github.com/care-git/vernier-news/commit/de507a99768bf6953f89d0edc1d8e62f0a82b7ad))

### Documentation

- Update markdown plan to reflect stage completion
  ([`2f5bfb1`](https://github.com/care-git/vernier-news/commit/2f5bfb1e31dbceb6243ea56fc75a86ae87947f55))


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
