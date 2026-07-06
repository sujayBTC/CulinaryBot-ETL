from celery import Celery
from celery.schedules import crontab

# BEAT_SCHEDULE = {
#     "recipe-ingest": {
#         "task": "data_pipelines.recipe_ingest.tasks.recipe_ingest_task",
#         "schedule": crontab(hour=2, minute=1),
#     },
#     "recipe-keyword-extraction": {
#         "task": "data_pipelines.recipe_keyword.tasks.recipe_keyword_extraction_task",
#         "schedule": crontab(hour=3, minute=0),
#     },
# }

celery_app = Celery(
    "elt-pipeline",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    # include=["data_pipelines.tasks.recipe_ingest","data_pipelines.tasks.keyword_pipeline"]
    include=[
        "data_pipelines.recipe_worker.keyword_worker",
        "data_pipelines.tasks.recipe_ingest"
        ]
)

# celery_app.conf.beat_schedule = BEAT_SCHEDULE
