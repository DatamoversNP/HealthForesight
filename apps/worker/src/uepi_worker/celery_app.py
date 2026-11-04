"""Celery application instance (no task imports — avoids circular import under prefork)."""
from celery import Celery
from kombu import Exchange, Queue

from uepi_worker.config import get_settings

settings = get_settings()

redis_url = settings.redis.url
if redis_url.startswith("rediss://") and "ssl_cert_reqs" not in redis_url:
    separator = "&" if "?" in redis_url else "?"
    redis_url = f"{redis_url}{separator}ssl_cert_reqs=CERT_NONE"

app = Celery(
    "uepi_worker",
    broker=redis_url,
    backend=redis_url,
)

_default_ex = Exchange("celery", type="direct")
_analytics_ex = Exchange("policy_analytics", type="direct")
_interactive_ex = Exchange("interactive", type="direct")

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_default_queue="celery",
    task_queues=(
        Queue("celery", _default_ex, routing_key="celery"),
        Queue("policy_analytics", _analytics_ex, routing_key="policy_analytics"),
        Queue("interactive", _interactive_ex, routing_key="interactive"),
    ),
    task_routes={
        "uepi_worker.tasks.policy_analytics_lifecycle_job": {
            "queue": "policy_analytics",
        },
        "uepi_worker.tasks.policy_analytics_probe_job": {
            "queue": "policy_analytics",
        },
        "uepi_worker.tasks.policy_impact_job": {"queue": "policy_analytics"},
        "uepi_worker.tasks.whatif_scenario_job": {"queue": "interactive"},
        "uepi_worker.tasks.export_pdf_job": {"queue": "interactive"},
        "uepi_worker.tasks.export_pptx_job": {"queue": "interactive"},
    },
    task_annotations={
        "uepi_worker.tasks.policy_analytics_lifecycle_job": {
            "rate_limit": "30/m",
            "soft_time_limit": 120,
            "time_limit": 150,
        },
        "uepi_worker.tasks.policy_analytics_probe_job": {
            "rate_limit": "120/m",
            "soft_time_limit": 45,
            "time_limit": 60,
        },
    },
    broker_transport_options={
        "visibility_timeout": 3600,
    },
    include=[
        "uepi_worker.tasks",
    ],
)
