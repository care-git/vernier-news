from app.worker import celery_app


@celery_app.task(name="pipeline.ingest_feeds")
def ingest_feeds() -> dict:
    """Fetch all active RSS/Atom feeds and run each article through the pipeline."""
    ...


@celery_app.task(name="pipeline.cluster_pass")
def cluster_pass() -> dict:
    """Assign any unclustered articles to clusters."""
    ...


@celery_app.task(name="pipeline.categorise_pending")
def categorise_pending() -> dict:
    """Run Ollama categorisation on any uncategorised articles."""
    ...


@celery_app.task(name="pipeline.precompute_digests")
def precompute_digests() -> dict:
    """Pre-compute and cache digest summaries for all active user preference profiles."""
    ...


@celery_app.task(name="pipeline.precompute_cluster_summaries")
def precompute_cluster_summaries() -> dict:
    """Pre-compute and cache cluster summary cards."""
    ...
