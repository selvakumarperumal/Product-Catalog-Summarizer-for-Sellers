# Celery setup
from celery import Celery
import os

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery_app = Celery(
    "ProductCatalogSummarizer",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_routes={
        "app.celery_app.tasks.*": {"queue": "default"}
    },
    task_ack_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=300
)

from app.celery_app import tasks