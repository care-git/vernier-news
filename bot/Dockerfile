FROM python:3.12-slim

WORKDIR /app

# Minimal image — the bot only needs the Telegram library and an HTTP client.
# It deliberately does NOT reuse the main app image (which pre-downloads MiniLM
# and spaCy) since it talks to the API over HTTP, not the database directly.
RUN pip install --no-cache-dir \
    "python-telegram-bot[job-queue]>=21" \
    "pydantic-settings>=2.3.0" \
    "httpx>=0.27.0"

COPY bot ./bot

CMD ["python", "-m", "bot.main"]
