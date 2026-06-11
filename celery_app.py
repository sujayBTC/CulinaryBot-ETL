from celery import Celery

from data_pipelines.beat_schedule import BEAT_SCHEDULE

celery_app = Celery(
    "elt-pipeline",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

celery_app.conf.beat_schedule = BEAT_SCHEDULE

import data_pipelines.recipe_ingest.tasks  # noqa: F401, E402
import data_pipelines.recipe_keyword.tasks  # noqa: F401, E402
