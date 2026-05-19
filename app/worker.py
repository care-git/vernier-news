from celery import Celery

from app.config import settings

celery_app = Celery("vernier_news", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "ingest-feeds": {
            "task": "pipeline.ingest_feeds",
            "schedule": 1800.0,  # every 30 minutes
        },
        "categorise-pending": {
            "task": "pipeline.categorise_pending",
            "schedule": 1800.0,  # every 30 minutes
        },
        "precompute-cluster-summaries": {
            "task": "pipeline.precompute_cluster_summaries",
            "schedule": 3600.0,  # every hour
        },
        "precompute-digests": {
            "task": "pipeline.precompute_digests",
            "schedule": 3600.0,  # every hour
        },
    },
)

celery_app.autodiscover_tasks(["app.pipeline"])
