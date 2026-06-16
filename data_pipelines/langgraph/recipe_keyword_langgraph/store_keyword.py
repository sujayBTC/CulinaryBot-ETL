from datetime import datetime

from langgraph.graph import END
from langgraph.types import Command

from data_pipelines.core.config import RECIPES_COLLECTION
from data_pipelines.db.mongo import get_recipes_collection, get_collection

# collection = MONGO_DB["RECIPES_COLLECTION"]

collection = get_collection("keywords")


def store_keywords(state):
    print("processed data =====>>",state["processed_data"])
    print("Reached store keywords==========================================>>>>>>>>>>>>>>>>>>>>>>>>.",state)
    collection.update_one(
        {"_id": state["execution_id"]},
        {"$set": {"keywords": state["processed_data"]}},
        {"$setOnInsert": {
            "cdate": datetime.utcnow()
        }},
        upsert=True,
    )
    print("Added keywords in the MongoDB================================>>>>>>>>>>>>>>>>")
    return Command(goto=END)
