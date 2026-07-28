from pydantic_settings import BaseSettings, SettingsConfigDict

# Embedding model — the shared substrate for dedup, clustering, and categorisation.
# Deliberately module constants rather than env settings: the dimension defines the
# pgvector column width, so changing either requires a migration + full re-embed.
# bge-m3 is multilingual (same story in different languages embeds close together)
# and measures ~2GB resident in fp32, which fits the VPS without quantisation.
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days
    refresh_token_expire_minutes: int = 43200  # 30 days

    app_env: str = "development"
    app_debug: bool = False

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"

    # API connector keys — all optional; connectors silently skip if unset
    guardian_api_key: str | None = None
    gnews_api_key: str | None = None
    currents_api_key: str | None = None
    nyt_api_key: str | None = None

    # Admin API key — protects /api/v1/admin/* endpoints
    admin_api_key: str | None = None

    # GDELT sweep query. The DOC API requires a query and supports no wildcard, so a
    # broad operator is needed to sweep general coverage. Kept in config rather than
    # hardcoded because tuning it changes ingest breadth and wants trying on the box
    # without a redeploy.
    gdelt_query: str = "sourcelang:eng"

    # CORS — comma-separated origins; add http://localhost:PORT for local Flutter dev
    cors_origins: str = "https://vernier.news"


settings = Settings()
