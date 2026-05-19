---
name: vernier-ingest
description: Trigger an immediate Vernier News feed ingestion run outside the normal 30-minute schedule. Use when asked to run an ingest, fetch new articles, or manually trigger the pipeline.
---

Queue an immediate ingest_feeds task and report the task ID. Call this skill when the user asks to "run an ingest", "fetch articles now", "trigger the pipeline", or similar.

Execute: `bash {baseDir}/scripts/run.sh`

Report the task ID and confirm the ingest has been queued. Note that ingestion runs asynchronously — the task has been queued, not completed. The user can check results with the health skill after a minute or two.
