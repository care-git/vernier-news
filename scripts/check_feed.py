"""Check whether RSS/Atom feed URLs are live and actively publishing.

    docker compose exec api python -m scripts.check_feed URL [URL ...]

Uses feedparser — the same library the ingest pipeline uses — so a feed that
parses here will parse at ingest. Run it from the VPS (the `api` container): many
outlets' bot protection blocks other fetchers but not the ingester, so this is the
authoritative liveness test.

The most-recent-entry date is what distinguishes a live feed from an abandoned one
that still returns valid XML (e.g. a feed whose newest item is a year old).
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

import feedparser


def check(url: str) -> None:
    parsed = feedparser.parse(url)
    status = getattr(parsed, "status", "?")
    entries = parsed.entries
    title = (parsed.feed.get("title") or "(no feed title)")[:40]

    latest: datetime | None = None
    for entry in entries:
        parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
        if parsed_time:
            dt = datetime(*parsed_time[:6], tzinfo=UTC)
            latest = dt if latest is None else max(latest, dt)

    if latest is not None:
        age_days = (datetime.now(UTC) - latest).days
        recency = f"latest {latest:%Y-%m-%d} ({age_days}d ago)"
    else:
        recency = "no dated entries"

    ok = len(entries) > 0
    flag = "OK  " if ok else "DEAD"
    print(f"{flag} http={status} entries={len(entries):<3} {title:<40} {recency}")
    if parsed.bozo and parsed.bozo_exception:
        # Many live feeds set bozo for harmless encoding quirks — informational only.
        print(f"     note: {type(parsed.bozo_exception).__name__}: {parsed.bozo_exception}")
    print(f"     {url}")


def main() -> None:
    urls = sys.argv[1:]
    if not urls:
        print("usage: python -m scripts.check_feed URL [URL ...]")
        raise SystemExit(1)
    for url in urls:
        check(url)


if __name__ == "__main__":
    main()
