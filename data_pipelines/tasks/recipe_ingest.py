import httpx
from data_pipelines.db.mongo import upsert_recipe_batch
from logger import logger

from data_pipelines.core.base import run_async
from data_pipelines.core.celery import celery_app
from data_pipelines.core.config import BACK_END_URL


async def run_recipe_ingest() -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(BACK_END_URL)
        response.raise_for_status()

    recipe_data = response.json()
    recipes = recipe_data.get("data", [])

    logger.info(f"Fetched recipes from backend status={response.status_code}")

    if not recipes:
        logger.warning("No recipes returned from backend")
        return {"upserted_count": 0}

    upserted_count = upsert_recipe_batch(recipes)
    logger.info(f"Recipe ingest complete upserted_count={upserted_count}")
    return {"upserted_count": upserted_count}


@celery_app.task(name="data_pipelines.recipe_ingest.tasks.recipe_ingest_task")
def recipe_ingest():
    return run_async(run_recipe_ingest())
