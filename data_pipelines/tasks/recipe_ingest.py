import httpx
from data_pipelines.db.mongo import upsert_recipe_batch, get_collection
from logger import logger

from data_pipelines.core.base import run_async
from data_pipelines.core.celery import celery_app
from data_pipelines.core.config import BACK_END_URL

METADATA_COLLECTION = "metadata"

async def run_recipe_ingest() -> dict:
    print("log 1 ========>")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BACK_END_URL}/recipes")
        response.raise_for_status()

    recipe_data = response.json()
    
    recipes = recipe_data.get("items", [])
    
    print("recipes===>",recipes)

    logger.info(f"Fetched recipes from backend status={response.status_code}")

    if not recipes:
        logger.warning("No recipes returned from backend")
        return {"upserted_count": 0}

    upserted_count = upsert_recipe_batch(recipes)
    print("upsert successfully ========>")
    logger.info(f"Recipe ingest complete upserted_count={upserted_count}")
    return {"upserted_count": upserted_count}

async def send_metadata():
    limit = 100
    skip = 0
    
    metadata_collection = get_collection(METADATA_COLLECTION)
    
    pending_recipe = metadata_collection.find_one({
    "status": {
        "$in": ["pending", "failed"]
    }
    })
    
    print("pending_recipe====>",pending_recipe)
    
    if not pending_recipe:
            # try:
                while True:
                    batch = list(
                        metadata_collection.find()
                        .skip(skip)
                        .limit(limit)
                    )
                    print("batch====>",batch)
                    batch1 = {
                        "data":batch
                    }
                    print("BACK_END_URL====>",BACK_END_URL)
                    async with httpx.AsyncClient() as client:
                        response = await client.post(f"{BACK_END_URL}/recipes/metadata", data=batch1)
                        response.raise_for_status()
                        
                        print("response===>",response)

                    if not batch:
                        break
                    
                    skip += limit
                    
            # except Exception as e:
            #     print("ERROR: ",e)
    else:
        print("something went wrong")
    
@celery_app.task(name="data_pipelines.recipe_ingest.tasks.recipe_ingest_task")
def recipe_ingest():
    return run_async(run_recipe_ingest())

@celery_app.task(name="data_pipelines.recipe_ingest.tasks.send_metadata_task")
def send_metadata_task():
    return run_async(send_metadata())