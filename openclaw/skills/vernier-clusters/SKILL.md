---
name: vernier-clusters
description: Report Vernier News clustering activity over the last 24 hours — how many clusters were created, updated, or have gone dormant. Use when asked about clustering stats, story clusters, or pipeline activity.
---

Fetch clustering stats for the last 24 hours and report them. Call this skill when the user asks about "clusters", "clustering stats", "how many stories", "pipeline activity", or similar.

Execute: `bash {baseDir}/scripts/run.sh`

Report: clusters created in the last 24 hours, clusters that received new articles (updated) in the last 24 hours, and clusters that have had no new articles for over 48 hours (dormant).
