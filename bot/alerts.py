from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.admin_client import AdminError
from bot.formatting import format_health

log = logging.getLogger("bot.alerts")


async def daily_digest_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Push the health summary to the alert chat once a day."""
    config = context.bot_data["config"]
    client = context.bot_data["admin_client"]
    chat_id = config.telegram_alert_chat_id
    if not chat_id:
        return
    try:
        text = "🗞 <b>Daily digest</b>\n" + format_health(await client.health())
    except AdminError as exc:
        text = f"🗞 <b>Daily digest</b>\n{exc.user_message}"
    await context.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)


async def threshold_alert_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Poll health and alert on entry/exit of unhealthy states (de-duplicated)."""
    config = context.bot_data["config"]
    client = context.bot_data["admin_client"]
    chat_id = config.telegram_alert_chat_id
    if not chat_id:
        return

    state = context.bot_data.setdefault(
        "alert_state",
        {"active": set(), "last_article_count": None, "last_change": datetime.now(UTC)},
    )
    active: set[str] = state["active"]

    async def notify(text: str) -> None:
        await context.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)

    # 1. API reachability.
    try:
        data = await client.health()
    except AdminError as exc:
        if "api_down" not in active:
            active.add("api_down")
            await notify(f"🔴 <b>Alert:</b> {exc.user_message}")
        return
    if "api_down" in active:
        active.discard("api_down")
        await notify("🟢 <b>Recovered:</b> API reachable again")

    # 2. Celery queue depth.
    depth = data["redis"]["celery_queue_depth"]
    if depth > config.bot_queue_depth_threshold:
        if "queue_depth" not in active:
            active.add("queue_depth")
            await notify(
                f"🔴 <b>Alert:</b> Celery queue depth {depth:,} "
                f"exceeds {config.bot_queue_depth_threshold:,}"
            )
    elif "queue_depth" in active:
        active.discard("queue_depth")
        await notify(f"🟢 <b>Recovered:</b> Celery queue depth back to {depth:,}")

    # 3. Ingestion progress — the article count should advance over time.
    articles = data["database"]["articles"]
    now = datetime.now(UTC)
    if state["last_article_count"] is None or articles != state["last_article_count"]:
        state["last_article_count"] = articles
        state["last_change"] = now
        if "ingest_stall" in active:
            active.discard("ingest_stall")
            await notify(f"🟢 <b>Recovered:</b> ingestion advancing again ({articles:,} articles)")
        return
    stalled_for = now - state["last_change"]
    if (
        stalled_for > timedelta(hours=config.bot_ingest_stall_hours)
        and "ingest_stall" not in active
    ):
        active.add("ingest_stall")
        await notify(
            f"🔴 <b>Alert:</b> no new articles in over "
            f"{config.bot_ingest_stall_hours}h — ingestion may be stalled"
        )
