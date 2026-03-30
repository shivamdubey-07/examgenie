from celery import Celery

from app.common.config import require_env

BROKER_URL = require_env("CELERY_BROKER_URL")
RESULT_BACKEND = require_env("CELERY_RESULT_BACKEND")

celery_app = Celery(
    "examgenie",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

celery_app.autodiscover_tasks(["app.worker.tasks"])
