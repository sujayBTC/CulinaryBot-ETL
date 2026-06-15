import json
from typing import Optional
from langgraph.types import Command
import tiktoken

from data_pipelines.db.mongo import ensure_indexes, get_recipes_collection
from data_pipelines.llm.state_manager import State

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


def create_token_chunks(recipes: list[dict]) -> list[list[dict]]:
    """
    Split recipes into chunks that fit within MAX_CHUNK_TOKENS.

    Args:
        recipes: List of recipe dictionaries

    Returns:
        List of recipe chunks, where each chunk is a list of recipes
    """
    chunks = []
    current_chunk = []
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

        # Start new chunk if current one is full
        if current_tokens + recipe_tokens > MAX_CHUNK_TOKENS:
            if current_chunk:  # Only append if non-empty
                chunks.append(current_chunk)
            current_chunk = [recipe]
            current_tokens = recipe_tokens
        else:
            current_chunk.append(recipe)
            current_tokens += recipe_tokens

    # Append final chunk
    if current_chunk:
        chunks.append(current_chunk)

    if skipped_count > 0:
        print(f"Skipped {skipped_count} oversized recipes")

    return chunks


async def fetch_recipe_node(state: State) -> State:
    """
    Fetch and process recipes from MongoDB, chunked by token count.

    This function:
    1. Retrieves recipes from MongoDB (once, cached in state)
    2. Deduplicates by name
    3. Removes unwanted fields
    4. Chunks recipes based on token count
    5. Sets the current chunk based on current_chunk_index

    Args:
        state: State dictionary with optional 'current_chunk_index' key

    Returns:
        Updated state with recipe chunks and current chunk info

    Raises:
        IndexError: If current_chunk_index exceeds available chunks
        KeyError: If MongoDB documents lack required structure
    """
    print("Fetch Recipe Node Triggered ===============>>>>>")
    current_index = state.get("current_chunk_index", 0)

    # Initialize chunks only once
    if "recipe_chunks" not in state:
        try:
            ensure_indexes()
            collection = get_recipes_collection()
            recipes = []

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
            recipe_chunks = create_token_chunks(unique_recipes)

            # Logging
            print(f"✓ Fetched recipes: {len(recipes)}")
            print(f"✓ Unique recipes: {len(unique_recipes)}")
            print(f"✓ Chunks created: {len(recipe_chunks)}")

            if recipe_chunks:
                total_chunk_tokens = sum(
                    count_tokens(r) for chunk in recipe_chunks for r in chunk
                )
                print(f"✓ Total tokens across all chunks: {total_chunk_tokens}")

            state["recipe_chunks"] = recipe_chunks

        except Exception as e:
            print(f"Error fetching recipes: {e}")
            state["recipe_chunks"] = []
            raise

    recipe_chunks = state["recipe_chunks"]

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
        goto="generate_keywords"
    )
