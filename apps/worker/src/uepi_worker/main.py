"""UEPI Worker Service entrypoint."""
from uepi_worker.celery_app import app

# Register tasks (tasks imports app from celery_app — no cycle)
import uepi_worker.tasks  # noqa: F401

if __name__ == "__main__":
    app.start()
