import json
from typing import Optional
from langgraph.types import Command
import tiktoken
from bson import ObjectId

from data_pipelines.db.mongo import ensure_indexes, get_recipes_collection, get_collection
from data_pipelines.langgraph.state_manager import State

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
encoder = tiktoken.encoding_for_model(MODEL_NAME)


def count_tokens(data: dict) -> int:
    """Count tokens in a JSON-serialized dictionary."""
    text = json.dumps(data, default=str, ensure_ascii=False)
    return len(encoder.encode(text))

BATCH = {
  "job_id": "",
  "chunk_index": 0,
  "recipe_ids": []
}

chunks_ids_collection = get_collection("chunks_details")

def create_token_chunks(job_id,recipes: list[dict]) -> list[list[dict]]:

    chunks = []
    chunk_ids = []
    current_chunk = []
    current_chunk_ids = []
    current_tokens = 0
    skipped_count = 0
    
    
    print("MAX_CHUNK_TOKENS======>",MAX_CHUNK_TOKENS)

    for recipe in recipes:
        recipe_tokens = count_tokens(recipe)

        # Handle recipes larger than chunk size
        if recipe_tokens > MAX_CHUNK_TOKENS:
            recipe_name = recipe.get("name", "Unknown")
            print(
                f"Skipping recipe '{recipe_name}' "
                f"because it exceeds token limit "
                f"({recipe_tokens} > {MAX_CHUNK_TOKENS} tokens)"
            )
            skipped_count += 1
            continue
        recipe_id = recipe.get("_id",0)
        
        # Start new chunk if current one is full
        if current_tokens + recipe_tokens > MAX_CHUNK_TOKENS:
            if current_chunk:  # Only append if non-empty
                chunks.append(current_chunk)
                chunk_ids.append(current_chunk_ids)
            if current_chunk_ids:
                batch = BATCH.copy()
                batch["job_id"] = job_id
                batch["chunk_index"] = BATCH["chunk_index"] + 1
                batch["recipe_ids"] = current_chunk_ids
                
            current_chunk = [recipe]
            current_chunk_ids = [recipe_id]
            current_tokens = recipe_tokens
        else:
            current_chunk.append(recipe)
            batch = BATCH.copy()
            current_chunk_ids.append(recipe_id)
            current_tokens += recipe_tokens

    # Append final chunk
    if current_chunk:
        chunks.append(current_chunk)
        
    if current_chunk_ids:
        batch = BATCH.copy()
        batch["job_id"] = job_id
        batch["chunk_index"] = BATCH["chunk_index"] + 1
        batch["recipe_ids"] = current_chunk_ids
        chunk_ids.append(batch)

    if skipped_count > 0:
        print(f"Skipped {skipped_count} oversized recipes")
        
    return_response = {
        "chunks": chunks,
        "chunks_ids": chunk_ids
    }

    return return_response


async def fetch_recipe_node(state: State) -> State:
    print("Fetch Recipe Node Triggered ===============>>>>>")
    current_index = state.get("current_chunk_index", 0)
    chunk_count = state.get("total_chunks", 0)
    job_id = state["execution_id"]
    # Initialize chunks only once
    
    keyword_collection = get_collection("keyword")
    
    total_chunk = keyword_collection["total_chunks"]
    last_proccesed_chunk = keyword_collection["current_chunk_index"]
    
    if total_chunk != last_proccesed_chunk:
        ensure_indexes()
        recipe_collection = get_recipes_collection()
        
        recipe_ids = chunks_ids_collection.find_one({"chunk_index": last_proccesed_chunk})
        
        cursor = recipe_collection.find(
            {
                "_id": {
                    "$in": [ObjectId(id_) for id_ in recipe_ids]
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
        
        cleaned_recipes = []
        
        for recipe in recipes:
            cleaned_recipe = {
                        key: value
                        for key, value in recipes.items()
                        if key not in UNWANTED_FIELDS
                    }
            cleaned_recipes.append(cleaned_recipe)
        
        return Command(
            update={
                "current_chunk" : cleaned_recipes,
                "current_chunk_index" : last_proccesed_chunk,
                "total_chunks" : total_chunk,
            },
            goto="generate_keywords"
        )
        
    
    if chunk_count == 0:
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
            chunk_data = create_token_chunks(job_id,unique_recipes)
            
            recipe_chunks = chunk_data["chunks"]
            
            recipe_chunk_ids = chunk_data["chunks_ids"]
            
            chunks_ids_collection.insert_many(recipe_chunk_ids)

            print("recipe_id===========>",recipe_chunk_ids)
            
            # Logging
            print(f"✓ Fetched recipes: {len(recipes)}")
            print(f"✓ Unique recipes: {len(unique_recipes)}")
            print(f"✓ Chunks created: {len(recipe_chunks)}")
            
            if recipe_chunks:
                total_chunk_tokens = sum(
                    count_tokens(r) for chunk in recipe_chunks for r in chunk
                )
                print(f"✓ Total tokens across all chunks: {total_chunk_tokens}")

        except Exception as e:
            print(f"Error fetching recipes: {e}")
            state["recipe_chunks"] = []
            raise

    # Validate current_index
    if not recipe_chunks:
        print("No recipe chunks available")
        state["current_chunk"] = []
        state["current_chunk_index"] = 0
        state["total_chunks"] = 0
        return state

    if current_index >= len(recipe_chunks):
        raise IndexError(
            f"current_chunk_index {current_index} exceeds "
            f"available chunks ({len(recipe_chunks)})"
        )

    # Set current chunk info
    state["current_chunk"] = recipe_chunks[current_index]
    state["current_chunk_index"] = current_index
    state["total_chunks"] = len(recipe_chunks)
    state["current_chunk_tokens"] = count_tokens({"recipes": state["current_chunk"]})

    return Command(
        update={
            "current_chunk" : recipe_chunks[current_index],
            "current_chunk_index" : current_index,
            "total_chunks" : len(recipe_chunks),
            "current_chunk_tokens" : count_tokens({"recipes": state["current_chunk"]})
        },
        goto="generate_keywords"
    )
