---
name: vernier-health
description: Check Vernier News pipeline health — DB row counts, Redis cache stats, and Celery queue depth. Use when asked about system status, health, how many articles have been ingested, cache state, or queue depth.
---

Run the health check script and report the results. Call this skill when the user asks any of: "health", "status", "how's the pipeline", "how many articles", "queue depth", or similar.

Execute: `bash {baseDir}/scripts/run.sh`

Report all returned values clearly: article and cluster counts from the database, how many summaries and digests are cached in Redis, and the current Celery queue depth.
