from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

celery_app = Celery(
    "elt-pipeline",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=[
        "data_pipelines.recipe_worker.keyword_worker",
        "data_pipelines.tasks.recipe_ingest",
        "data_pipelines.tasks.user_preference_task",
        "data_pipelines.test.test_tasks"
        ]
)


celery_app.conf.timezone = "Asia/Kolkata"
celery_app.conf.enable_utc = False

celery_app.conf.beat_schedule = {
"user-preference-pipeline": {
        "task": "data_pipelines.test.test_tasks.run_user_preference_pipeline",
        "schedule": crontab(hour=17, minute=5),
    },
"recipe-keyword-pipeline": {
        "task": "data_pipelines.test.test_tasks.start_keyword_pipeline",
        "schedule": crontab(hour=14, minute=0),
    },
"smart-grocery-pipeline": {
        "task": "data_pipelines.test.test_tasks.run_smart_grocery_pipeline",
        "schedule": crontab(hour=11, minute=33),
    }
}