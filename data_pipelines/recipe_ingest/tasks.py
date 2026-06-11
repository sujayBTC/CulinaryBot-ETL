from celery_app import celery_app
from data_pipelines.base import run_async
from data_pipelines.recipe_ingest.pipeline import run_recipe_ingest


@celery_app.task(name="data_pipelines.recipe_ingest.tasks.recipe_ingest_task")
def recipe_ingest_task():
    return run_async(run_recipe_ingest())
