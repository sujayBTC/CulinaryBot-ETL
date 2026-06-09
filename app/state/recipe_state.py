# graph/state.py

from typing import TypedDict

class RecipeState(TypedDict):
    recipe_id: int
    recipe: dict
    metadata: dict