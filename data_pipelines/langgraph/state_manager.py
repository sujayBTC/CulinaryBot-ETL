from typing import List, Literal, TypedDict
from uuid import uuid4

class State(TypedDict, total=False):
    execution_id: str
    current_chunk: List[dict]
    total_chunks: int
    current_chunk_index: int
    current_chunk_tokens: int
    processed_data: List[str]

class RecipeState(TypedDict, total=False):
    execution_id: str
    recipe: dict
    recipe_id: int
    total_recipe: int
    current_recipe_index: int
    processed_recipe: int 
    processed_data: List[str]