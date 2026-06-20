from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from data_pipelines.llm.model import llm
from data_pipelines.langgraph.state_manager import State
from langgraph.types import Command
from data_pipelines.db.mongo import get_collection
from data_pipelines.llm.prompt import KEYWORDS_EXTRACT_PROMPT
import json
collection = get_collection("keywords")

class RecipeKeywords(BaseModel):
    keywords: list[str]

def generate_keywords(state: State):
    chunk = state["current_chunk"]
    current_chunk_index = state.get("current_chunk_index", 0)
    total_chunk = state["total_chunks"]
    existing_keywords = state.get("processed_data", [])
    
    if not existing_keywords:
        last_doc = collection.find_one(
                    sort=[("_id", -1)]
                )
        existing_keywords = []
        if last_doc:
            existing_keywords = last_doc.get("keywords", [])
    
    print("existing_keywords=================>", existing_keywords)

    prompt = KEYWORDS_EXTRACT_PROMPT
    
    gemini_prompt = """
        You are an expert culinary data analyst. Your task is to analyze a recipe chunk and generate a single, consolidated list of all unique classification keywords found across ALL the recipes combined.

        Analyze every single recipe provided. Do not stop after the first few. Ensure you capture keywords for the non-veg recipes and dessert recipes included in the batch.

        Rules for the keyword list:
        - Combine all keywords into ONE single global list.
        - Do not repeat keywords (ensure the list contains only unique values).
        - Do not include synonyms or duplicate-meaning words.
        - Return ONLY a valid JSON object. Do not include markdown code blocks (like ```json), introductory text, or explanations.

        Categories to consider when extracting keywords:
        1. Diet Type: Veg, Non-Veg, Eggitarian, Vegan
        2. Dietary/Allergen Restrictions: Gluten-Free, Dairy-Free, Nut-Free, Keto, Low-Carb, Diabetic-Friendly
        3. Meal Type: Breakfast, Dessert, Appetizer, Main Course, Snack, Side Dish

        Output Format (Return ONLY this exact JSON structure):
        {
        "keywords": ["Veg", "Non-Veg", "Dessert", "Breakfast", "Gluten-Free"]
        }
                
    """
    
    RECIPE_KEYWORD_PROMPT = """
        You are an expert culinary data analyst. You will be given a CHUNK of recipe data
        containing multiple recipes, each with ingredients and method/instructions.

        TASK:
        Analyze EVERY recipe in the chunk — do not stop after the first few, and do not skip
        non-veg, eggitarian, or dessert recipes. For each recipe, infer which keywords apply
        using the rules below. Then merge all inferred keywords across all recipes into ONE
        single deduplicated list.

        ================================
        HOW TO INFER EACH CATEGORY
        ================================

        1. Diet Type (pick the one that applies per recipe, based on ingredients):
        - "Non-Veg" → contains chicken, mutton, beef, pork, fish, prawns, shrimp, crab,
            squid, any meat, seafood, or gelatin.
        - "Eggitarian" → contains egg/eggs but no meat or seafood.
        - "Vegan" → contains no animal products at all (no meat, egg, dairy, honey, ghee).
        - "Veg" → contains dairy and/or vegetables but no meat, fish, or egg.
        (A recipe gets exactly one of these four, never more than one.)

        2. Dietary / Allergen Restrictions (apply ALL that fit, a recipe can have several):
        - "Gluten-Free" → no wheat, maida, flour, semolina/rava, breadcrumbs, pasta, soy
            sauce, or barley/malt anywhere in ingredients.
        - "Dairy-Free" → no milk, cream, butter, cheese, paneer, ghee, yogurt/curd.
        - "Nut-Free" → no almonds, cashews, peanuts, walnuts, pistachios, nut butters,
            or nut oils/milks.
        - "Keto" / "Low-Carb" → very low in sugar, rice, flour, potatoes, or other starches;
            high in fat/protein (e.g., mostly meat, eggs, cheese, leafy vegetables, nuts).
        - "Diabetic-Friendly" → low/no added sugar, no refined flour or white rice as a
            primary ingredient, no sugary syrups.

        3. Meal Type (pick the one that best fits, based on method/context, not just ingredients):
        - "Breakfast" → eggs, oats, porridge, pancakes, toast, idli/dosa, smoothies, etc.,
            or explicitly described as a morning dish.
        - "Dessert" → sweet dishes, cakes, puddings, ice cream, sweets/mithai, contains
            sugar/jaggery/chocolate as a defining ingredient and is not a savory main.
        - "Appetizer" → small bites, starters, finger foods, soups served before a main.
        - "Main Course" → substantial dishes meant as the central part of a meal (curries,
            biryanis, pasta mains, roasts).
        - "Snack" → light, casual eats not tied to a specific meal (chaat, namkeen, chips).
        - "Side Dish" → accompaniments (raita, chutney, salad, dal served alongside a main).

        ================================
        RULES
        ================================
        - Process every recipe in the chunk individually first (mentally), then combine.
        - Combine all keywords into ONE single global list — do not group by recipe.
        - No duplicates. No synonyms or near-duplicate meanings (e.g., do not include both
        "Sweet" and "Dessert" — prefer the category term defined above).
        - If the chunk contains at least one recipe with ingredients/method text, the output
        list must NOT be empty — every recipe yields at least a Diet Type and a Meal Type.
        - Only use keywords from the categories defined above. Do not invent new keywords.
        - Return ONLY a valid JSON object — no markdown fences, no commentary, no preamble.

        ================================
        OUTPUT FORMAT (return exactly this structure, nothing else)
        ================================
        {{
        "keywords": ["Veg", "Non-Veg", "Dessert", "Breakfast", "Gluten-Free"]
        }}
        """
    

    # structured_llm = llm.with_structured_output(RecipeKeywords)

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
    
    print("llm response====>", response)

    # result = response.get("keywords", [])
    result = json.loads(response.content)


    return Command(
        update ={
            "processed_data" : result,
            "current_chunk_index": current_chunk_index+1
        },
        goto="chunk_orchestrator"
    )
