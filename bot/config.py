from pydantic_settings import BaseSettings, SettingsConfigDict


class BotConfig(BaseSettings):
    """Runtime configuration for the Telegram control bot.

    Values are read from environment variables (see .env / .env.example). Fields
    default to empty/neutral values so the object can be constructed in tests; the
    entry point (main) validates that the required values are present before start.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = ""
    telegram_allowed_user_ids: str = ""
    telegram_alert_chat_id: str | None = None

    admin_api_key: str | None = None
    bot_api_base_url: str = "http://api:8000"

    bot_digest_utc_hour: int = 8
    bot_alert_poll_minutes: int = 15
    bot_queue_depth_threshold: int = 100
    bot_ingest_stall_hours: int = 3

    @property
    def allowed_user_ids(self) -> set[int]:
        """Parse the comma-separated allowlist into a set of Telegram user IDs."""
        return {int(part) for part in self.telegram_allowed_user_ids.split(",") if part.strip()}
