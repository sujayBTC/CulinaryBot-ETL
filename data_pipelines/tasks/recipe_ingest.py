import httpx
from data_pipelines.db.mongo import upsert_recipe_batch, get_collection
from logger import logger
import json

from data_pipelines.core.base import run_async
from data_pipelines.core.celery import celery_app
from data_pipelines.core.config import BACK_END_URL

METADATA_COLLECTION = "metadata"

async def run_all_recipe_ingest() -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BACK_END_URL}/all-recipes")
        response.raise_for_status()

    recipe_data = response.json()
    
    recipes = recipe_data.get("items", [])

    logger.info(f"Fetched recipes from backend status={response.status_code}")

    if not recipes:
        logger.warning("No recipes returned from backend")
        return {"upserted_count": 0}

    upserted_count = upsert_recipe_batch(recipes)

    logger.info(f"Recipe ingest complete upserted_count={upserted_count}")
    return {"upserted_count": upserted_count}



async def run_today_recipe_ingest() -> dict:
    print("step 4 =====================> RUN TODAY RECIPE INGEST")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BACK_END_URL}/today-recipes")
        response.raise_for_status()

    recipe_data = response.json()
    
    recipes = recipe_data.get("items", [])

    logger.info(f"Fetched recipes from backend status={response.status_code}")

    if not recipes:
        logger.warning("No recipes returned from backend")
        return {"upserted_count": 0}

    upserted_count = upsert_recipe_batch(recipes)
    logger.info(f"Recipe ingest complete upserted_count={upserted_count}")
    return {"upserted_count": upserted_count}



async def send_recipe_metadata():
    print("STEP 6 ====================> SEND RECIPE METADATA")
    limit = 100
    skip = 0
    
    metadata_collection = get_collection(METADATA_COLLECTION)
    
    # pending_recipe = metadata_collection.find_one({
    # "status": {
    #     "$in": ["pending", "failed"]
    # }
    # })
    
    # if not pending_recipe:
    try:
        while True:
            batch = list(
                metadata_collection.find(
                    {
                        "status":"success"
                    },{
                    "_id":0,
                    "created_at": 0,
                    "completed_at": 0,
                    "status":0,
                    "time_taken_seconds":0
                })
                .skip(skip)
                .limit(limit)
            )

            if not batch:
                break
            
            batch_data = {"data": batch}
            payload =json.dumps(batch_data)
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{BACK_END_URL}/recipes/metadata", json=payload)
                response.raise_for_status()

            skip += limit
            
    except Exception as e:
        print("ERROR: ",e)
    # else:
    #     print("no recipe to send")
    
    
async def triger_convert_vector():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BACK_END_URL}/add-vectors-in-pgvector")
        response.raise_for_status()


    logger.info(f"triger convert vector end-point, backend status={response.status_code}")

    return {"upserted_count": response}



@celery_app.task(name="data_pipelines.recipe_ingest.tasks.all_recipe_ingest_task")
def all_recipe_ingest_task():
    return run_async(run_all_recipe_ingest())

@celery_app.task(name="data_pipelines.recipe_ingest.tasks.send_metadata_task")
def send_metadata_task():
    return run_async(send_recipe_metadata())

@celery_app.task(name="data_pipelines.recipe_ingest.tasks.today_recipe_ingest_task")
def today_recipe_ingest_task():
    return run_async(run_today_recipe_ingest())

@celery_app.task(name="data_pipelines.recipe_ingest.tasks.triger_conver_vector_task")
def triger_conver_vector_task():
    return run_async(triger_convert_vector())