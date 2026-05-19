from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080   # 7 days
    refresh_token_expire_minutes: int = 43200  # 30 days

    app_env: str = "development"
    app_debug: bool = False

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"


settings = Settings()
