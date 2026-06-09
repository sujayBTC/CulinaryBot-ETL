# import asyncio
# import json
# from typing import List
# from datetime import datetime, timedelta
# from collections import defaultdict
# from pydantic import BaseModel

# from db_services import DBRecordService
# from database import get_database_session
# from app.schemas import (
#     ChatSchema,
#     UserSchema,
#     UserUpdateSchema,
# )
# from app.models import ChatModel, UserModel
# from langchain_core.messages import HumanMessage, SystemMessage
# from app.llm.model import llm
# from app.core.celery import celery_app

# from app.core.logger import get_logger

# logger = get_logger(__name__)

# class FoodPreference(BaseModel):
#     food: str
#     source: str


# class FavoriteDish(BaseModel):
#     dish: str
#     source: str


# class DietaryPreference(BaseModel):
#     dietary: str
#     source: str


# class HealthCondition(BaseModel):
#     condition: str
#     source: str
    
# class UserPreferenceSchema(BaseModel):
#     food_preference: List[FoodPreference] = []
#     favorite_dishes: List[FavoriteDish] = []
#     dietary_preferences: List[DietaryPreference] = []
#     health_conditions: List[HealthCondition] = []
#     processed: datetime


# async def extract_json():
#     async for db in get_database_session():
#         today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
#         print("today_start==>",today_start)
#         tomorrow_start = today_start + timedelta(days=1)
        
#         custom_filters = [ChatModel.created_at >= today_start, ChatModel.created_at < tomorrow_start]
        
#         print("custom_filters==>",custom_filters)
#         response = await DBRecordService.fetch_records(
#             db=db,
#             model=ChatModel,
#             schema=ChatSchema,
#             custom_filters=custom_filters,
#         )
        
#         result = extract_message(response["data"])
        
#         result1 = remove_duplicates(result)
        
#         group_users = group_by_user(result1)
        
#         for single_user in group_users.keys():
            
#             user_messages = group_users[single_user]
            
#             chunks = list(chunk_messages(user_messages, chunk_size=4))
            
#             final_preference = None 
            
#             for chunk in chunks:
#                 print(f"Processing chunk for user {single_user}: and chunk {chunk}")
#                 final_preference = await call_llm(chunk, previous_context=final_preference)
        
#             print(f"Final aggregated preference for {single_user}: {final_preference}")
            
#             params = {"phone_number" : single_user}
#             user = await DBRecordService.get_one_record_by_params(
#                 db=db,
#                 schema=UserSchema,
#                 model=UserModel,
#                 params=params
#             )
            
#             if user and user["data"]:
#                 meta_data = (user["data"].meta_data or {}).copy()
#                 meta_data.update({"user_preference": final_preference.model_dump(mode="json")})
                
#                 output = await DBRecordService.update_record(
#                     db=db,
#                     schema=UserSchema,
#                     model=UserModel,
#                     record_id=user["data"].id,
#                     update_data=UserUpdateSchema(meta_data=meta_data)
#                 )

#                 logger.info("ETL Result", output=output)
        
# def extract_message(rows):
#     extracted = []
    
#     for row in rows:
#         try:
#             value = row.content["entry"][0]["changes"][0]["value"]
#             user_id = value["contacts"][0]["wa_id"]
            
#             for msg in value.get("messages", []):
#                 msg_type = msg.get("type")
                
#                 if msg_type == "text":
#                         text = msg["text"]["body"]

#                 elif msg_type == "interactive":
#                     text = msg["interactive"]["button_reply"]["title"]

#                 else:
#                     continue
            
#             extracted.append({
#                 "user_id": user_id,
#                 "message": text,
#                 "type": msg_type,
#                 "timestamp": int(msg["timestamp"]),
#             })
#         except Exception:
#             continue
    
#     return extracted

# def remove_duplicates(messages):
#     seen = set()
#     unique = []

#     for m in messages:
#         key = (m["user_id"], m["message"].lower())
#         if key not in seen:
#             seen.add(key)
#             unique.append(m)

#     return unique

# def group_by_user(messages):
#     user_map = defaultdict(list)

#     for m in messages:
#         user_map[m["user_id"]].append({
#             "role": "user",
#             "content": m["message"]
#         })

#     return user_map

# def chunk_messages(messages: List[dict], chunk_size: int = 10):
#     """Yield successive n-sized chunks from messages."""
#     for i in range(0, len(messages), chunk_size):
#         yield messages[i : i + chunk_size]
        


# async def call_llm(data, previous_context=None) -> dict:
    
#     if not previous_context:
#         previous_context = json.dumps({
#             "food_preference": [{
#                 "food":"",
#                 "source":""
#                 }],
#             "favorite_dishes": [
#                     {
#                         "dish":"",
#                         "source":"",
#                     },
#                     {
#                         "dish":"",
#                         "source":"",
#                     }
#                 ],
#             "dietary_preferences": [
#                     {
#                         "dietary":"",
#                         "source":"",
#                     }
#                 ],
#             "health_conditions": [
#                     {
#                         "condition":"",
#                         "source":"",
#                     }
#                 ],
#             "processed": datetime.utcnow().isoformat(),
#         })

    
    
#     gemini_system_prompt = """
#             You are an expert AI data extraction assistant specializing in analyzing chat histories to determine user food profiles.

#             Your sole task is to extract food preferences, restrictions, and health conditions from the provided chat history and format them into a strict, valid JSON object.

#             ### JSON Schema Requirement:
#             Return the data EXACTLY in this JSON structure. Do not include markdown formatting (like ```json ... 
#             ```), trailing commas, or any conversational filler.

#             {
#                 "food_preferences": [
#                     {
#                         "food": "Example: Italian, spicy food, seafood",
#                         "preference_type": "like OR dislike",
#                         "source": "Exact quote from chat history"
#                     }
#                 ],
#                 "favorite_dishes": [
#                     {
#                         "dish": "Example: Pizza, Sushi",
#                         "source": "Exact quote from chat history"
#                     }
#                 ],
#                 "dietary_restrictions": [
#                     {
#                         "dietary": "Example: Vegan, Keto, Halal, High-Protein",
#                         "source": "Exact quote from chat history"
#                     }
#                 ],
#                 "health_conditions": [
#                     {
#                         "condition": "Example: Diabetes, Peanut Allergy, Lactose Intolerant",
#                         "source": "Exact quote from chat history"
#                     }
#                 ],
#                 "last_processed_utc": "YYYY-MM-DDTHH:MM:SSZ"
#             }

#             ### Execution Steps:
#             1. **Analyze:** Carefully read the chat history. Identify explicitly stated food preferences (likes/dislikes), specific favorite dishes, dietary choices, and health/medical conditions related to food.
#             2. **Verify:** Ensure the information is explicitly stated by the user. Do not assume, infer, or hallucinate any details. If the chat history does not mention a category, leave that specific array empty `[]`.
#             3. **Timestamp:** Set the "last_processed_utc" to the current UTC timestamp if provided in the context, otherwise use the current date placeholder.
#             4. **Output:** Return ONLY the raw JSON object. Do not wrap it in markdown blocks. Do not add introductory or concluding text.
#         """
    
        
#     user_prompt = f"NEW_MESSAGES to analyze: {json.dumps(data)}"

        
#     structured_llm = llm.with_structured_output(UserPreferenceSchema)
    
#     response = await structured_llm.ainvoke(
#         [
#             SystemMessage(content=system_prompt),
#             HumanMessage(content=user_prompt),
#         ]
#     )
    
#     return response


# @celery_app.task
# def extract_user_preference():
#     asyncio.run(extract_json())