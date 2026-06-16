from langgraph.graph import END
from langgraph.types import Command

from data_pipelines.core.config import RECIPES_COLLECTION
from data_pipelines.db.mongo import  get_collection

# collection = MONGO_DB["RECIPES_COLLECTION"]

collection = get_collection("recipe_metadata")


def recipe_metadata_store(state):
    print("processed data =====>>",state["processed_data"])
    collection.update_one(
        {"_id": state["execution_id"]},
        {"$set": {"recipe_id": state["recipe_id"]}},
        {"$set": {"metadata": state["processed_data"]}},
        upsert=True,
    )
    
    return Command(goto=END)
