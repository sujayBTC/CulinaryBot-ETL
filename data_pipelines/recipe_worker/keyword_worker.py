from data_pipelines.core.celery import celery_app
from bson import ObjectId
from data_pipelines.db.mongo import recipe_collection,audit_collection
from pydantic import BaseModel
from data_pipelines.llm.prompt import SINGLE_RECIPE_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage
from data_pipelines.llm.model import llm
from datetime import datetime
import asyncio
import time
from data_pipelines.db.mongo import keywords_collection
class RecipeWithKeywords(BaseModel):
    keywords: dict


async def run_keywords_generator(recipe_id_str):
    try:
        recipe_id = ObjectId(recipe_id_str)
        recipe = recipe_collection.find_one(
            {"_id": recipe_id}
        )

        if not recipe:
            audit_collection.insert_one(
                {
                    "recipe_id": recipe_id,
                    "task": "keyword_generation",
                    "status": "FAILED",
                    "error_type": "RecipeNotFound",
                    "error_message": f"Recipe {recipe_id} not found",
                    "created_at": datetime.utcnow(),
                }
            )
            return

        # if recipe.get("keyword_status") == "success":
        #     return

        keywords_collection.insert_one(
            {
            "_id": recipe_id,
            "keyword_status": "processing",
            "created_at": datetime.utcnow()
            }
        )
        recipe_for_llm = {
                    k: v
                    for k, v in recipe.items()
                    if k not in [
                        "_id",
                        "created_at",
                        "updated_at"
                    ]
                }
        structured_llm = llm.with_structured_output(RecipeWithKeywords)

        recipe_start_time = time.perf_counter()
        response = await structured_llm.ainvoke(
            [
                SystemMessage(content=SINGLE_RECIPE_PROMPT),
                HumanMessage(
                        content=f"Recipe:\n{recipe_for_llm}"
                    )
                
            ]
        )

        print(response.keywords)
        keys = response.keywords
        recipe_time_taken = time.perf_counter() - recipe_start_time
        keywords_collection.update_one(
            {"_id": recipe_id},
            {
                "$set": {
                    "keywords": keys,
                    "keyword_status": "success",
                    "time_taken_seconds": round(recipe_time_taken, 2),
                    "completed_at": datetime.utcnow()
                }
            }
        )

    except Exception as e:

        keywords_collection.update_one(
            {"_id": recipe_id},
            {
                "$set": {
                    "keyword_status": "failed"
                }
            }
        )

        audit_collection.insert_one(
            {
                "recipe_id": recipe_id,
                "task": "keyword_generation",
                "status": "FAILED",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "created_at": datetime.utcnow(),
            }
        )

        raise

@celery_app.task()
def keywords_generator(recipe_id_str):
    asyncio.run(run_keywords_generator(recipe_id_str))
