"""Minimal Celery client for sending tasks to the worker (no uepi_worker import)."""
from functools import lru_cache
from typing import Any, List, Optional

from celery import Celery

from uepi_api.config import get_settings


@lru_cache(maxsize=1)
def _get_celery_app() -> Celery:
    settings = get_settings()
    redis_url = settings.redis.url
    if redis_url.startswith("rediss://") and "ssl_cert_reqs" not in redis_url:
        sep = "&" if "?" in redis_url else "?"
        redis_url = f"{redis_url}{sep}ssl_cert_reqs=CERT_NONE"
    app = Celery(
        "uepi_api_client",
        broker=redis_url,
        backend=redis_url,
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )
    return app


def send_task(name: str, args: Optional[List[Any]] = None, kwargs: Optional[dict] = None, **opts) -> Any:
    """Send a task to the worker by name (no import of uepi_worker)."""
    app = _get_celery_app()
    return app.send_task(name, args=args or [], kwargs=kwargs or {}, **opts)
