import asyncio
import httpx

from pymongo import UpdateOne

from data_pipelines.db.mongo import get_collection
from data_pipelines.core.celery import celery_app
from data_pipelines.core.config import BACK_END_URL
from data_pipelines.langgraph.smart_grocery_pipeline.smart_grocery_pipeline import smart_grocery_extraction

RECIPE_BRAND = "recipe_brand"

async def recie_brand_ingest():
    
    print("step 1 ============> RECIPE BRAND INGEST")
    limit = 100
    offset = 0
    while True:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACK_END_URL}/get-all-brand?limit={limit}&offset={offset}")
            
            response.raise_for_status()
            
            conversation_data = response.json()

            
            user_preference_keyword_collection = get_collection(RECIPE_BRAND)

            
            items = conversation_data.get("brands", [])
            
            if not items:
                break            
                            
            operations = [
                UpdateOne({"id": item["id"]}, {"$set": item}, upsert=True)
                for item in items
            ]

            user_preference_keyword_collection.bulk_write(operations)
    
            if not conversation_data["brands"]:
                break
                
            offset += limit

@celery_app.task
def recie_brand_ingest_task():
    asyncio.run(recie_brand_ingest())

@celery_app.task
def smart_grocery_task():
    asyncio.run(smart_grocery_extraction())

