"""
Celery application configuration.

Step 12:
- Redis broker
- Redis result backend
- task discovery
"""

from celery import Celery

from config import settings


celery_app = Celery(
    "ai_doc_screening",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "tasks.pipeline",
    ],
)


celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)