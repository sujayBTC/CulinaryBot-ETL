import json
from typing import Optional
from langgraph.types import Command
import tiktoken

from data_pipelines.db.mongo import ensure_indexes, get_recipes_collection, get_collection
from data_pipelines.langgraph.state_manager import State
from langgraph.graph import END
from celery import current_task

UNWANTED_FIELDS = {
    "created_at",
    "updated_at",
    "deleted_at",
    "created_by_id",
    "updated_by_id",
    "recipe_form_id",
}

# Example for a 128k context model
MODEL_NAME = "gpt-4o"
MODEL_CONTEXT_WINDOW = 128_000
RESERVED_TOKENS = (
    5_000  # system prompt
    + 20_000  # existing keyword dictionary
    + 5_000  # expected response
    + 8_000  # safety buffer
)
MAX_CHUNK_TOKENS = MODEL_CONTEXT_WINDOW - RESERVED_TOKENS
# MAX_CHUNK_TOKENS = 5000
encoder = tiktoken.encoding_for_model(MODEL_NAME)


BATCH = {
  "job_id": "",
  "chunk_index": 0,
  "recipe_ids": [],
  "status":"pending"
}

chunks_ids_collection = get_collection("chunks_details")

def count_tokens(data: dict) -> int:
    """Count tokens in a JSON-serialized dictionary."""
    text = json.dumps(data, default=str, ensure_ascii=False)
    return len(encoder.encode(text))

def create_token_chunks(job_id,recipes: list[dict]) -> list[list[dict]]:

    chunks = []
    chunk_ids = []
    
    current_chunk = []
    current_chunk_ids = []
    current_tokens = 0
    chunk_index = 0
    skipped_count = 0
    

    for recipe in recipes:
        recipe_tokens = count_tokens(recipe)

        if recipe_tokens > MAX_CHUNK_TOKENS:
            recipe_name = recipe.get("name", "Unknown")
            print(
                f"Skipping recipe '{recipe_name}' "
                f"because it exceeds token limit "
                f"({recipe_tokens} > {MAX_CHUNK_TOKENS} tokens)"
            )
            skipped_count += 1
            continue
        recipe_id = recipe.get("_id")

        if current_tokens + recipe_tokens > MAX_CHUNK_TOKENS:
            if current_chunk:
                chunks.append(current_chunk)

            if current_chunk_ids:
                chunk_ids.append({
                    "job_id": job_id,
                    "chunk_index": chunk_index,
                    "recipe_ids": current_chunk_ids.copy(),
                    "status": "pending"
                })
                chunk_index += 1
                
            current_chunk = [recipe]
            current_chunk_ids = [recipe_id]
            current_tokens = recipe_tokens
        else:
            current_chunk.append(recipe)
            current_chunk_ids.append(recipe_id)
            current_tokens += recipe_tokens

    if current_chunk:
        chunks.append(current_chunk)
        
    if current_chunk_ids:
        chunk_ids.append({
            "job_id": job_id,
            "chunk_index": chunk_index,
            "recipe_ids": current_chunk_ids.copy(),
            "status": "pending"
        })


    if skipped_count > 0:
        print(f"Skipped {skipped_count} oversized recipes")

    return chunk_ids

skip = 0

async def fetch_recipe_node(state: State) -> State:
    global recipe_chunk_ids
    global skip

    current_index = state.get("current_chunk_index", 0)
    chunk_count = state.get("total_chunks", 0)
    job_id = state["execution_id"]

    keyword_collection = get_collection("keywords")
    last_proccess_keyword = keyword_collection.find_one({"_id": str(job_id)})
    
    if last_proccess_keyword:
        status = last_proccess_keyword["status"]
    
        if status == "incomplete":
            total_chunk = last_proccess_keyword["total_chunks"]
            if skip == 0:
                last_proccesed_chunk = last_proccess_keyword["current_chunk_index"] + 1
                skip = 1
            else:
                last_proccesed_chunk = current_index
                
            if total_chunk != last_proccesed_chunk:

                
                chunk_details = chunks_ids_collection.find_one({
                    "job_id": job_id,
                    "chunk_index": last_proccesed_chunk
                    })
                
                recipe_ids = chunk_details["recipe_ids"]
                
                return Command(
                    update={
                        "current_chunk" : recipe_ids,
                        "current_chunk_index" : last_proccesed_chunk,
                        "total_chunks" : total_chunk,
                    },
                    goto="generate_keywords"
                )
        
        if status == "complete":
            return Command(goto=END)
    
    if len(recipe_chunk_ids) == 0:
        try:
            ensure_indexes()
            collection = get_recipes_collection()
            recipes = []

            # Fetch all recipes from MongoDB
            for doc in collection.find({}):
                try:
                    record = {
                        "_id": str(doc["_id"]),
                        **doc.get("payload", {}),
                        **doc.get("enrichments", {}),
                    }
                    recipes.append(record)
                except (KeyError, TypeError) as e:
                    print(f"Skipping malformed document: {e}")
                    continue

            # Deduplicate recipes by name
            unique_recipes = []
            seen_recipe_names = set()

            for recipe in recipes:
                recipe_name = recipe.get("name", "").strip().lower()

                # Skip recipes with empty names
                if not recipe_name:
                    continue

                # Skip duplicate names
                if recipe_name in seen_recipe_names:
                    continue

                seen_recipe_names.add(recipe_name)

                # Remove unwanted fields
                cleaned_recipe = {
                    key: value
                    for key, value in recipe.items()
                    if key not in UNWANTED_FIELDS
                }
                unique_recipes.append(cleaned_recipe)

            # Create token-based chunks
            recipe_chunk_ids = create_token_chunks(job_id,unique_recipes)
            
            chunks_ids_collection.insert_many(recipe_chunk_ids)

        except Exception as e:
            print(f"Error fetching recipes: {e}")
            state["recipe_chunks"] = []
            raise

    return Command(
        update={
            "current_chunk" : recipe_chunk_ids[current_index]["recipe_ids"],
            "current_chunk_index" : current_index,
            "total_chunks" : len(recipe_chunk_ids),
            "current_chunk_tokens" : count_tokens({"recipes": state["current_chunk"]})
        },
        goto="generate_keywords"
    )
