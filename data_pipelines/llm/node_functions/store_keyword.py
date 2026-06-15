from langgraph.graph import END
from langgraph.types import Command

from data_pipelines.core.config import RECIPES_COLLECTION
from data_pipelines.db.mongo import get_recipes_collection

# collection = MONGO_DB["RECIPES_COLLECTION"]

collection = get_recipes_collection()


def store_keywords(state):

    collection.update_one(
        {"_id": state["execution_id"]},
        {"$set": {"keywords": state["processed_data"]}},
        upsert=True,
    )

    return Command(goto=END)
