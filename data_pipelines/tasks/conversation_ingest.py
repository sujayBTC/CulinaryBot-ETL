import httpx

from data_pipelines.db.mongo import get_collection
from data_pipelines.core.base import run_async
from data_pipelines.core.celery import celery_app
from data_pipelines.core.config import BACK_END_URL


CONVERSATION_COLLECTION = "conversations"
USER_PREFERENCE_KEYWORD = "user_preference_keyword"

def remove_fields(obj):
    """Recursively remove 'confidence' and 'evidence' keys."""
    if isinstance(obj, dict):
        return {
            key: remove_fields(value)
            for key, value in obj.items()
            if key not in ("confidence", "evidence")
        }
    elif isinstance(obj, list):
        return [remove_fields(item) for item in obj]
    else:
        return obj

async def conersation_ingest():
    
    print("step 1 ============> CONVERSATION INGEST")
    limit = 100
    offset = 0
    while True:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACK_END_URL}/user/all-conversations?limit={limit}&offset={offset}")
            
            response.raise_for_status()
            
            conversation_data = response.json()

            
            user_preference_keyword_collection = get_collection(CONVERSATION_COLLECTION)

            
            if conversation_data["items"]:
                user_preference_keyword_collection.insert_many(conversation_data["items"])
    
            if not conversation_data["items"]:
                break
                
            offset += limit


async def send_keyword():
    print("step 3 ============> SEND KEYWORD")
    limit = 100
    skip = 0
    
    user_preference_keyword_collection = get_collection(USER_PREFERENCE_KEYWORD)
    
    while True:
        batch_response = list(
            user_preference_keyword_collection.find(
                {},
                {
                    "user_id": 1,
                    "user_preferences": 1,
                    "_id": 0,
                }
            )
            .skip(skip)
            .limit(limit)
        )
        
        if not batch_response:
            break

        cleaned_batch_response = [remove_fields(doc) for doc in batch_response]
        
        batch = {
            "data": cleaned_batch_response
        }

        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{BACK_END_URL}/user-preference", json=batch)

            response.raise_for_status()
            
            skip += limit