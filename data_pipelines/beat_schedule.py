from celery.schedules import crontab

BEAT_SCHEDULE = {
    "recipe-ingest": {
        "task": "data_pipelines.recipe_ingest.tasks.recipe_ingest_task",
        "schedule": crontab(hour=2, minute=0),
    },
    "recipe-keyword-extraction": {
        "task": "data_pipelines.recipe_keyword.tasks.recipe_keyword_extraction_task",
        "schedule": crontab(hour=3, minute=0),
    },
}
