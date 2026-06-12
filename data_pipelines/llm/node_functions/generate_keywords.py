from langchain_core.messages import HumanMessage, SystemMessage

from data_pipelines.llm.model import llm
from data_pipelines.llm.state_manager import State
from langgraph.types import Command

def generate_keywords(state: State):
    chunk = state["current_chunk"]
    current_chunk_index = state.get("current_chunk_index", 0)
    existing_keywords = state.get("processed_data", [])

    prompt = f"""
                    RECIPE KEYWORD DICTIONARY MANAGER
            Purpose: Maintain a consistent, immutable global keyword dictionary for recipe categorization across a dataset. Keywords map recipes to consistent categories.
            Core Rules:

            Existing keywords are immutable — never modify, rename, delete, or replace existing keywords
            Reuse before creating — always check if a concept already exists before adding new keywords
            Only add new keywords — output only keywords that don't exist in the current dictionary
            Consistency over completeness — prefer one standardized keyword over multiple variations

            Keyword Guidelines:

            Format: lowercase, singular nouns, short phrases (1-2 words max)
            Examples: vegetarian, non-vegetarian, lunch, breakfast, grilling, dairy-free, spicy, dessert
            Avoid: duplicates, synonyms, recipe-specific noise, overly specific variations

            Valid Keyword Categories:

            Dietary restrictions/preferences (e.g., vegan, gluten-free, dairy-free)
            Meal type (e.g., breakfast, lunch, dinner, snack)
            Protein type (e.g., chicken, beef, fish, lentil)
            Cuisine type (e.g., indian, italian, thai)
            Cooking method (e.g., grilled, baked, fried, steamed)
            Flavor profile (e.g., spicy, sweet, umami)
            Main ingredient (e.g., rice, pasta, potato)
            Equipment (e.g., oven, stovetop, blender)

            Input Format:
            json{
            "existing_keywords": ["veg", "non-veg", "lunch", "breakfast"],
            "recipe_text": "..."
            }
            Output Format:
            json{
            "new_keywords": ["keyword1", "keyword2"]
            }
            Example:
            Input:
            json{
            "existing_keywords": ["veg", "non-veg", "lunch", "breakfast"],
            "recipe_text": "Grilled chicken with garlic butter for dinner"
            }
            Output:
            json{
            "new_keywords": ["chicken", "grilled", "dinner"]
            }
    """

    response = llm.invoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content=f"""
                Existing Global Keyword Dictionary:
                {existing_keywords}

                Recipe Chunk:
                {chunk}
                
            """),
        ]
    )
    result = response.content()

    return Command(
        update ={
            "processed_data" : result,
            "current_chunk_index": current_chunk_index+1
        },
        goto="chunk_orchestrator"
    )
