from langgraph.graph import END
from langgraph.types import Command

from data_pipelines.core.config import MONGO_DB

collection = MONGO_DB["keywords"]


def store_keywords(state):

    collection.update_one(
        {"_id": state["execution_id"]},
        {"$set": {"keywords": state["processed_data"]}},
        upsert=True,
    )

    return Command(goto=END)
