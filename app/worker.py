from celery import Celery

from app.config import settings

app = Celery("vernier_news", broker=settings.redis_url, backend=settings.redis_url)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# Phase 1: ingestion tasks will be registered here
