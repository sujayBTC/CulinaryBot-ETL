import asyncio

from db.mongo import ensure_indexes, get_recipes_collection
from utils.utils import State

CHUNK_SIZE = 20

UNWANTED_FIELDS = {
    "created_at",
    "updated_at",
    "deleted_at",
    "created_by_id",
    "updated_by_id",
    "recipe_form_id",
}

current_index = 0
recipe_chunks = []

async def fetch_recipe_node(state: State) -> State:
    current_index = state.get("current_chunk_index", 0)
    
    if not recipe_chunks:
    
        ensure_indexes()
        collection = get_recipes_collection()

        unique_recipes = []
        seen_names = set()
        recipes = []

        for doc in collection.find({}):
            record = {**doc["payload"], **doc.get("enrichments", {})}
            recipes.append(record)

        for recipe in recipes:
            recipe_name = recipe.get("name", "").strip().lower()
            if not recipe_name or recipe_name in seen_names:
                continue

            seen_names.add(recipe_name)
            cleaned_recipe = {
                key: value for key, value in recipe.items() if key not in UNWANTED_FIELDS
            }
            unique_recipes.append(cleaned_recipe)

        recipe_chunks = [
            unique_recipes[i : i + CHUNK_SIZE]
            for i in range(0, len(unique_recipes), CHUNK_SIZE)
        ]

    print(f"Original Recipes: {len(recipes)}")
    print(f"Unique Recipes: {len(unique_recipes)}")
    print(f"Chunks: {len(recipe_chunks)}")
    
    state["current_chunk"] = recipe_chunks[current_index]
    state["current_chunk_index"] = current_index
    state["total_chunks"] = len(recipe_chunks)
    
    return state

