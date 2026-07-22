from __future__ import annotations

import logging
from datetime import UTC, time

from telegram.ext import Application, CommandHandler

from bot import alerts, handlers
from bot.admin_client import AdminClient
from bot.auth import build_user_filter
from bot.config import BotConfig

log = logging.getLogger("bot")


def build_application(config: BotConfig) -> Application:
    application = Application.builder().token(config.telegram_bot_token).build()
    application.bot_data["config"] = config
    application.bot_data["admin_client"] = AdminClient(
        config.bot_api_base_url, config.admin_api_key
    )

    user_filter = build_user_filter(config.allowed_user_ids)
    application.add_handler(CommandHandler("start", handlers.start_handler, filters=user_filter))
    application.add_handler(CommandHandler("help", handlers.help_handler, filters=user_filter))
    application.add_handler(CommandHandler("health", handlers.health_handler, filters=user_filter))
    application.add_handler(CommandHandler("ingest", handlers.ingest_handler, filters=user_filter))
    application.add_handler(
        CommandHandler("clusters", handlers.clusters_handler, filters=user_filter)
    )
    application.add_handler(
        CommandHandler("sources", handlers.sources_handler, filters=user_filter)
    )
    application.add_error_handler(handlers.error_handler)

    if config.telegram_alert_chat_id:
        job_queue = application.job_queue
        job_queue.run_daily(
            alerts.daily_digest_job,
            time=time(hour=config.bot_digest_utc_hour, tzinfo=UTC),
        )
        job_queue.run_repeating(
            alerts.threshold_alert_job,
            interval=config.bot_alert_poll_minutes * 60,
            first=config.bot_alert_poll_minutes * 60,
        )
        log.info(
            "Alerting enabled: daily digest at %02d:00 UTC, threshold poll every %dm",
            config.bot_digest_utc_hour,
            config.bot_alert_poll_minutes,
        )
    else:
        log.info("TELEGRAM_ALERT_CHAT_ID unset — proactive alerting disabled")

    return application


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = BotConfig()

    if not config.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set — cannot start.")
    if not config.allowed_user_ids:
        raise SystemExit("TELEGRAM_ALLOWED_USER_IDS is empty — refusing to start (fail closed).")

    application = build_application(config)
    log.info("Bot starting (allowlist: %d user(s))", len(config.allowed_user_ids))
    application.run_polling()


if __name__ == "__main__":
    main()
