from bot.formatting import (
    format_cluster_stats,
    format_health,
    format_ingest,
    format_sources,
)


def _health_payload() -> dict:
    return {
        "database": {
            "articles": 1204,
            "clusters": 812,
            "active_outlets": 31,
            "uncategorised_articles": 1204,
        },
        "redis": {
            "cluster_summaries_cached": 48,
            "digests_cached": 3,
            "celery_queue_depth": 0,
        },
    }


def test_format_health_includes_counts_with_thousands_separators():
    text = format_health(_health_payload())
    assert "Articles: 1,204" in text
    assert "Celery queue depth: 0" in text
    assert text.startswith("🩺")


def test_format_ingest_reports_task_id():
    text = format_ingest({"task_id": "abc-123", "status": "queued"})
    assert "abc-123" in text
    assert "/health" in text


def test_format_cluster_stats():
    text = format_cluster_stats({"period_hours": 24, "created": 14, "updated": 22, "dormant": 5})
    assert "Created: 14" in text
    assert "Dormant: 5" in text


def test_format_sources_lists_inactive_domains():
    text = format_sources(
        {
            "total": 31,
            "active": 30,
            "inactive": 1,
            "wire_services": 4,
            "inactive_domains": ["example.com"],
        }
    )
    assert "Total: 31" in text
    assert "example.com" in text


def test_format_sources_without_inactive_domains():
    text = format_sources(
        {"total": 31, "active": 31, "inactive": 0, "wire_services": 4, "inactive_domains": []}
    )
    assert "Inactive domains" not in text
