from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "elt-pipeline",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

import celery_task.recipe_task