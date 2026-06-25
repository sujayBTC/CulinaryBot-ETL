from datetime import datetime

from langgraph.graph import END
from langgraph.types import Command
from data_pipelines.langgraph.state_manager import State

from data_pipelines.core.config import RECIPES_COLLECTION
from data_pipelines.db.mongo import get_recipes_collection, get_collection

# collection = MONGO_DB["RECIPES_COLLECTION"]

chunk_collection = get_collection("chunks_details")
collection = get_collection("keywords")


def store_keywords(state: State):
    collection.update_one(
        {"_id": state["execution_id"]},
        {"$set": {
            "keywords": state["processed_data"],
            "status":"complete",
            "total_chunks": state["total_chunks"],
            "current_chunk_index": state["current_chunk_index"]
            },
            "$setOnInsert": {
            "cdate": datetime.utcnow()
        }},
        upsert=True,
    )
    
    chunk_collection.delete_many({"job_id": str(state["execution_id"])})

    return Command(goto=END)
