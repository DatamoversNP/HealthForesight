"""UEPI Worker Service"""
from celery import Celery
from uepi_worker.config import get_settings

settings = get_settings()

# Fix Redis URL for SSL if needed
redis_url = settings.redis.url
if redis_url.startswith("rediss://") and "ssl_cert_reqs" not in redis_url:
    # Add ssl_cert_reqs parameter for rediss:// URLs
    separator = "&" if "?" in redis_url else "?"
    redis_url = f"{redis_url}{separator}ssl_cert_reqs=CERT_NONE"

app = Celery(
    "uepi_worker",
    broker=redis_url,
    backend=redis_url,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Import tasks to register them
from uepi_worker.tasks import (  # noqa: F401, E402
    ingest_claims_job,
    policy_impact_job,
    substitution_job,
    provider_segmentation_job,
    whatif_scenario_job,
    elasticity_job,
    daily_data_and_observations_job,
    scorecard_job,
    export_pdf_job,
    export_pptx_job,
)

if __name__ == "__main__":
    app.start()

