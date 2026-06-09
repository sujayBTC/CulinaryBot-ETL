import httpx
import asyncio
from logger import logger

from app.db.db_services import DBRecordService
from app.model.models import Recipe

from app.db.database import get_database_session
from app.config import BACK_END_URL
from celery_app import celery_app

async def run():
    
    try:
        
        async with httpx.AsyncClient() as client:
            response = await client.get(BACK_END_URL)
        
        recipe_data = response.json()
            
        logger.info(f"fetch recipe {response.status_code}")
        
        recipes = recipe_data.get("data",[])
        
        if recipes:
            for db in get_database_session():
                try:
                    result = await DBRecordService.bulk_create_records(
                        db, 
                        Recipe, 
                        recipe_data["data"]
                    )
                    
                    print("result=====>",result)
                
                    logger.info("Insert Successfully")
                
                except Exception as e:
                    logger.exception(f"Failed to insert recipes ERROR:{e}")
        else:
            print("The reccipes empty")
                
        
    except Exception as e:
        logger.info(f"ERROR: {e}")
        
    

@celery_app.task
def recipe_task():
    return asyncio.run(run())