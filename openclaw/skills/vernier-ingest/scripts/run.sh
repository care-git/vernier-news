#!/bin/bash
set -euo pipefail
curl -sf -X POST -H "X-Admin-Key: ${VERNIER_ADMIN_KEY}" http://localhost:8000/api/v1/admin/ingest
