from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from data_pipelines.llm.model import llm
from data_pipelines.llm.state_manager import State
from langgraph.types import Command

class RecipeKeywords(BaseModel):
    keywords: list[str]

def generate_keywords(state: State):
    chunk = state["current_chunk"]
    current_chunk_index = state.get("current_chunk_index", 0)
    
    existing_keywords = state.get("processed_data", [])

    prompt = """
                    OBJECTIVE

        Extract recommendation and discovery keywords from recipes.

        The goal is NOT to create an ingredient index.

        The goal IS to create tags that help users discover similar recipes.

        PRIORITY ORDER

        1. Dietary profile
        2. Nutrition profile
        3. Flavor profile
        4. Meal occasion
        5. Cuisine
        6. Cooking style
        7. Texture
        8. Preparation style
        9. Serving context

        DO NOT EXTRACT

        * Ingredient names
        * Recipe names
        * Dish names
        * Brand names
        * Garnishes
        * Minor ingredients

        Examples:

        Chicken Biryani
        BAD:
        ["chicken","rice","onion","garam-masala"]

        GOOD:
        [
        "spicy",
        "aromatic",
        "high-protein",
        "indian",
        "lunch",
        "dinner",
        "one-pot",
        "rich",
        "festive",
        "non-vegetarian"
        ]

        Paneer Butter Masala
        BAD:
        ["paneer","butter","tomato"]

        GOOD:
        [
        "creamy",
        "rich",
        "vegetarian",
        "indian",
        "dinner",
        "protein-rich",
        "restaurant-style"
        ]

        KEYWORD CATEGORIES

        dietary_profile:
        [
        "vegetarian",
        "vegan",
        "non-vegetarian",
        "gluten-free",
        "dairy-free",
        "keto",
        "low-carb",
        "high-protein",
        "low-fat",
        "plant-based"
        ]

        meal_occasion:
        [
        "breakfast",
        "brunch",
        "lunch",
        "dinner",
        "snack",
        "party",
        "festive",
        "quick-meal",
        "family-meal"
        ]

        flavor_profile:
        [
        "spicy",
        "mild",
        "sweet",
        "savory",
        "tangy",
        "smoky",
        "rich",
        "creamy",
        "aromatic",
        "zesty",
        "earthy"
        ]

        cuisine_type:
        [
        "indian",
        "italian",
        "thai",
        "chinese",
        "mexican",
        "japanese",
        "mediterranean"
        ]

        preparation_style:
        [
        "one-pot",
        "slow-cooked",
        "restaurant-style",
        "street-food",
        "comfort-food",
        "home-style"
        ]

        texture_profile:
        [
        "crispy",
        "crunchy",
        "soft",
        "tender",
        "silky",
        "chewy"
        ]

        INFERENCE RULES

        * Infer tags even when not explicitly stated.

        * If chicken, fish, eggs, lamb, beef, seafood are present:
        add "non-vegetarian".

        * If recipe contains substantial protein:
        add "high-protein".

        * If multiple spices are used:
        add "spicy" and/or "aromatic".

        * If butter, cream, coconut milk, cheese, or rich sauces dominate:
        add "creamy" and/or "rich".

        * If typically eaten as a main meal:
        add "lunch" and/or "dinner".

        * If traditionally served at celebrations:
        add "festive".

        * If everything cooks in one vessel:
        add "one-pot".

        OUTPUT REQUIREMENTS

        Return only recommendation keywords.

        Do not return ingredient names unless the ingredient itself is the primary identity of the recipe category (rare exception).

        The final keyword list should describe HOW the recipe feels, WHEN it is eaten, WHO it suits, and WHAT type of food it is—not what ingredients it contains.

    """

    structured_llm = llm.with_structured_output(RecipeKeywords)

    response = structured_llm.invoke(
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
    
    print("llm response====>", response)

    
    # result = response.get("keywords", [])
    result = response.keywords


    return Command(
        update ={
            "processed_data" : result,
            "current_chunk_index": current_chunk_index+1
        },
        goto="chunk_orchestrator"
    )
