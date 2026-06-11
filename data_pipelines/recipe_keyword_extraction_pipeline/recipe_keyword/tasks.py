from celery_app import celery_app
from data_pipelines.base import run_async
from data_pipelines.recipe_keyword.pipeline import run_recipe_keyword_extraction


@celery_app.task(
    name="data_pipelines.recipe_keyword.tasks.recipe_keyword_extraction_task"
)
def recipe_keyword_extraction_task():
    return run_async(run_recipe_keyword_extraction())
