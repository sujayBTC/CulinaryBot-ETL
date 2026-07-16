import json
from typing import Optional
from langgraph.types import Command
import tiktoken

from data_pipelines.db.mongo import ensure_indexes, get_recipes_collection
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

recipes = []
unique_recipes = []


async def fetch_recipe_node_for_recipe(state: State) -> State:
    
    current_recipe_index = state["current_recipe_index"]

    # Initialize chunks only once
    if "recipe_chunks" not in state:
        try:
            ensure_indexes()
            collection = get_recipes_collection()

            # Fetch all recipes from MongoDB
            for doc in collection.find({}):
                try:
                    record = {
                        **doc.get("payload", {}),
                        **doc.get("enrichments", {}),
                    }
                    recipes.append(record)
                except (KeyError, TypeError) as e:
                    print(f"Skipping malformed document: {e}")
                    continue

            # Deduplicate recipes by name
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

            # Logging
            print(f"✓ Fetched recipes: {len(recipes)}")
            print(f"✓ Unique recipes: {len(unique_recipes)}")

        except Exception as e:
            print(f"Error fetching recipes: {e}")
            state["recipe_chunks"] = []
            raise

    # Set current chunk info
    state["recipe"] = recipe[current_recipe_index]
    state["total_recipe"] = len(recipe)

    return Command(
        goto="generate_keywords"
    )
