import httpx
import asyncio
from logger import logger

from app.db.db_services import DBRecordService
from app.model.models import Recipe

from app.db.database import get_database_session
from app.config import BACK_END_URL
from celery_app import celery_app

@celery_app.task(name="app.tasks.recipe")
async def get_recipe_node():
    
    try:
        url = f"{BACK_END_URL}/recipes"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        
        recipe_data = response.json()
        
        print("recipe_data==>",recipe_data["data"])
            
        logger.info(f"fetch recipe {response.status_code}")
        
        async for db in get_database_session():
            try:
                result = await DBRecordService.bulk_create_records(
                    db, 
                    Recipe, 
                    recipe_data["data"]
                )
            
                logger.info(f"Insert Successfully, Inserted count {result["data"].inserted_count}")
            
            except Exception as e:
                
                logger.exception("Failed to fetch recipes")
                
        
    except Exception as e:
        logger.info(f"fetch recipe {response.status_code}")
    

if __name__ == "__main__":
    asyncio.run(get_recipe_node())