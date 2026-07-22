from __future__ import annotations

import html


def format_health(data: dict) -> str:
    db = data["database"]
    cache = data["redis"]
    return (
        "🩺 <b>Pipeline health</b>\n"
        "<b>Database</b>\n"
        f"• Articles: {db['articles']:,}\n"
        f"• Clusters: {db['clusters']:,}\n"
        f"• Active outlets: {db['active_outlets']:,}\n"
        f"• Uncategorised: {db['uncategorised_articles']:,}\n"
        "<b>Redis</b>\n"
        f"• Cluster summaries cached: {cache['cluster_summaries_cached']:,}\n"
        f"• Digests cached: {cache['digests_cached']:,}\n"
        f"• Celery queue depth: {cache['celery_queue_depth']:,}"
    )


def format_ingest(data: dict) -> str:
    task_id = html.escape(str(data.get("task_id", "?")))
    return (
        f"✅ <b>Ingest queued</b> — task <code>{task_id}</code>\n"
        "Check /health in a minute or two."
    )


def format_cluster_stats(data: dict) -> str:
    return (
        "📊 <b>Clusters — last 24h</b>\n"
        f"• Created: {data['created']:,}\n"
        f"• Updated: {data['updated']:,}\n"
        f"• Dormant: {data['dormant']:,}"
    )


def format_sources(data: dict) -> str:
    lines = [
        "📡 <b>Sources</b>",
        f"• Total: {data['total']:,}",
        f"• Active: {data['active']:,}",
        f"• Inactive: {data['inactive']:,}",
        f"• Wire services: {data['wire_services']:,}",
    ]
    inactive = data.get("inactive_domains") or []
    if inactive:
        shown = inactive[:20]
        lines.append("<b>Inactive domains:</b>")
        lines.append(", ".join(html.escape(domain) for domain in shown))
        if len(inactive) > len(shown):
            lines.append(f"…and {len(inactive) - len(shown)} more")
    return "\n".join(lines)
