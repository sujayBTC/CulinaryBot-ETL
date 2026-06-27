from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from data_pipelines.llm.model import llm
from data_pipelines.langgraph.state_manager import State
from langgraph.types import Command

from data_pipelines.db.mongo import get_collection, ensure_indexes, get_recipes_collection
from data_pipelines.llm.prompt import KEYWORDS_EXTRACT_PROMPT

import json
from datetime import datetime

from bson import ObjectId

keyword_collection = get_collection("keywords")
chunks_ids_collection = get_collection("chunks_details")

class RecipeKeywords(BaseModel):
    keywords: list[str]

def generate_keywords(state: State):
    job_id = state["execution_id"]
    chunk = state["current_chunk"]
    current_chunk_index = state.get("current_chunk_index", 0)
    total_chunk = state["total_chunks"]
    existing_keywords = state.get("processed_data", [])
 
    try:
        ensure_indexes()
        recipe_collection = get_recipes_collection()
        
        cursor = recipe_collection.find(
                    {
                        "_id": {
                            "$in": [ObjectId(id_) for id_ in chunk]
                        }
                    }
                )
        recipes = [
            {
                **doc.get("payload", {}),
                **doc.get("enrichments", {}),
            }
            for doc in cursor
        ]
        
        if not existing_keywords:
            last_docs = keyword_collection.find_one(
                        {"_id":str(job_id)}
                    )
            
            if last_docs:
                existing_keywords = last_docs.get("keywords",[])

            prompt = KEYWORDS_EXTRACT_PROMPT   

            response = llm.invoke(
                [
                    SystemMessage(content=prompt),
                    HumanMessage(content=f"""
                        Existing Global Keyword Dictionary:
                        {existing_keywords}

                        Recipe Chunk:
                        {recipes}
                        
                    """),
                    
                ]
            )

            content = response.content.strip()

            if content.startswith("```json"):
                content = content.removeprefix("```json").strip()

            if content.endswith("```"):
                content = content.removesuffix("```").strip()

            result = json.loads(content)
            
            chunks_ids_collection.update_one(
                {"chunk_index":current_chunk_index},
                {"$set":{
                    "status":"complete"
                }}
                )
            
            return Command(
                update ={
                    "processed_data" : result,
                    "current_chunk_index": current_chunk_index+1
                },
                goto="chunk_orchestrator"
            )
            
    except Exception as e:
        keyword_collection.update_one(
            {"_id": state["execution_id"]},
            {"$set": {
                "current_chunk_index": current_chunk_index,
                "total_chunks": total_chunk,
                "status":"incomplete",
                "keyword": existing_keywords,
                },
                "$setOnInsert": {
                "cdate": datetime.utcnow()
            }},
        upsert=True,
        )