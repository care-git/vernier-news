from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.admin_client import AdminClient, AdminError
from bot.formatting import (
    format_cluster_stats,
    format_health,
    format_ingest,
    format_sources,
)

log = logging.getLogger("bot.handlers")

_COMMANDS = (
    "/health — pipeline health: DB, cache, queue\n"
    "/ingest — trigger an immediate feed ingest\n"
    "/clusters — cluster activity, last 24h\n"
    "/sources — outlet / source summary\n"
    "/help — show this list"
)


def _client(context: ContextTypes.DEFAULT_TYPE) -> AdminClient:
    return context.bot_data["admin_client"]


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Vernier control bot. Available commands:\n\n" + _COMMANDS
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(_COMMANDS)


async def health_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        data = await _client(context).health()
    except AdminError as exc:
        await update.effective_message.reply_text(exc.user_message)
        return
    await update.effective_message.reply_html(format_health(data))


async def ingest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        data = await _client(context).ingest()
    except AdminError as exc:
        await update.effective_message.reply_text(exc.user_message)
        return
    await update.effective_message.reply_html(format_ingest(data))


async def clusters_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        data = await _client(context).cluster_stats()
    except AdminError as exc:
        await update.effective_message.reply_text(exc.user_message)
        return
    await update.effective_message.reply_html(format_cluster_stats(data))


async def sources_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        data = await _client(context).sources()
    except AdminError as exc:
        await update.effective_message.reply_text(exc.user_message)
        return
    await update.effective_message.reply_html(format_sources(data))


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("Unhandled bot error", exc_info=context.error)
