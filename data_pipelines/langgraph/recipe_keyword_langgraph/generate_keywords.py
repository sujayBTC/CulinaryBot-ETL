from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from data_pipelines.llm.model import llm
from data_pipelines.langgraph.state_manager import State
from langgraph.types import Command
from data_pipelines.db.mongo import get_collection

collection = get_collection("keywords")

class RecipeKeywords(BaseModel):
    keywords: list[str]

def generate_keywords(state: State):
    chunk = state["current_chunk"]
    current_chunk_index = state.get("current_chunk_index", 0)
    
    existing_keywords = state.get("processed_data", [])
    
    if not existing_keywords:
        print("log 1=======================================================================>")
        last_docs = collection.find_one(
                    sort=[("_id", -1)]
                )
        existing_keywords = last_docs.get("keywords",[])
    
    print("existing_keywords=================>", existing_keywords)

    prompt = """
                # QUICK REFERENCE - ADVANCED KEYWORD EXTRACTION

        ## One-Minute Summary

        **What**: Extract 25-35 rich, contextual keywords from recipes
        **How**: Use advanced prompt with 12 keyword categories + 3 keyword types
        **Why**: Build immutable keyword dictionary for recipe discovery
        **Output**: JSON with new keywords, categories, and metrics

        ---

        ## The Three Types of Keywords to Extract

        ### 1. EXPLICIT Keywords (Directly Mentioned)
        - Ingredients (chicken, rice, paneer)
        - Cooking methods (grilled, slow-cooked, fried)
        - Equipment (oven, wok, air-fryer)

        **Example**: In "Chicken Biryani" → chicken, basmati-rice, slow-cooked

        ### 2. IMPLICIT Keywords (Inferred)
        - Dietary attributes (protein-rich, high-carb, low-fat)
        - Flavor profiles (spicy, aromatic, creamy)
        - Texture (tender-meat, fluffy-rice, crunchy)

        **Example**: In "Chicken Biryani" → protein-rich, aromatic, tender-chicken

        ### 3. CONTEXTUAL Keywords (Usage Context)
        - Occasions (party-favorite, festival-dish, celebration-meal)
        - Timing (quick-meal, slow-cook, make-ahead)
        - Audience (family-friendly, kid-friendly, crowd-pleaser)

        **Example**: In "Chicken Biryani" → festival-dish, celebration-meal, family-favorite

        ---

        ## 12 Keyword Categories

        | Category | Examples |
        |----------|----------|
        | Dietary & Health | vegan, high-protein, low-fat, dairy-free, organic |
        | Meal Type & Occasion | breakfast, dinner, party-food, celebration-meal, quick-lunch |
        | Protein Type | chicken, beef, tofu, lentil, paneer |
        | Cuisine & Regional | indian, thai, italian, mughlai-influenced, north-indian |
        | Cooking Method | grilled, baked, slow-cooked, stir-fried, pressure-cooked |
        | Flavor Profile | spicy, creamy, aromatic, sweet-sour-spicy, umami |
        | Main Ingredient | rice, pasta, noodle, yogurt-base, tomato-base |
        | Texture & Consistency | creamy, crunchy, tender, fluffy, thick-gravy |
        | Preparation Style | marinated, layered, one-pot, quick-prep, make-ahead |
        | Equipment | oven, wok, slow-cooker, instant-pot, cast-iron |
        | Time & Effort | quick-meal, 15-minute, slow-cook, labor-intensive |
        | Serving & Pairing | lunch-favorite, party-pleaser, crowd-favorite, reheatable |

        ---

        ## Keyword Format Rules

        ✅ **VALID**
        - `chicken` (1 word, lowercase)
        - `slow-cooked` (2 words, hyphenated)
        - `non-veg` (2 words, hyphenated)
        - `protein-rich` (2 words, hyphenated)
        - `festival-appropriate` (2 words, hyphenated)
        - `creamy-curry-base` (3 words max, hyphenated)

        ❌ **INVALID**
        - `Chicken` (capital letter)
        - `slow cooked` (space, should be hyphen)
        - `pad-thai` (recipe name - too specific)
        - `extremely-flavorful` (generic/marketing term)
        - `tikka_masala` (underscore, not hyphen)
        - `curry, rice, vegetables` (plural, avoid if singular exists)

        ---

        ## Target: 25-35 Keywords Per Recipe

        When processing recipes, aim for **25-35 keywords**:
        - ~3 from dietary/health
        - ~3 from meal type
        - ~2 from protein type
        - ~2 from cuisine
        - ~3 from cooking method
        - ~4 from flavor profile
        - ~2 from main ingredient
        - ~2 from texture
        - ~2 from preparation style
        - ~1 from equipment

        **Total: ~25-30 keywords per recipe**

        ---

        ## Input Format

        ```json
        {
        "existing_keywords": [
            "veg",
            "non-veg",
            "lunch",
            "chicken"
        ],
        "recipes": [
            {
            "name": "Recipe Name",
            "ingredients": "Full ingredient list with quantities",
            "instructions": "Step-by-step cooking instructions",
            "description": "Rich description of flavors, texture, occasion, etc."
            }
        ]
        }
        ```

        ---

        ## Expected Output Format

        ```json
        {
        "new_keywords": [
            "keyword1",
            "keyword2",
            "keyword3"
        ],
        "extracted_by_recipe": [
            {
            "recipe_name": "Recipe Name",
            "keywords_found": ["kw1", "kw2"],
            "keyword_count": 28,
            "categories": {
                "dietary_health": ["non-veg", "protein-rich"],
                "meal_type": ["lunch-friendly"],
                "protein_type": ["chicken"],
                ...
            }
            }
        ],
        "summary": {
            "total_recipes_processed": 1,
            "total_new_keywords": 28,
            "target_keyword_count": 30,
            "current_progress_percent": 93,
            "keywords_by_category": {
            "dietary_health": 2,
            "meal_type": 3,
            "protein_type": 1,
            ...
            }
        }
        }
        ```

        ---

        ## What to EXCLUDE ❌

        **Never include:**
        - Existing keywords (check list carefully)
        - Recipe names ("tikka-masala", "biryani")
        - Brand names ("coca-cola", "maggi")
        - Generic words ("delicious", "tasty", "nice")
        - Hyperbole ("mind-blowing", "heavenly")
        - Unclear terms ("stuff", "things")
        - Duplicates ("spicy" + "chili-hot")
        - Verbs ("cooking", "mixing")
        - Plurals (use singular form)

        ---

        ## What to INCLUDE ✅

        **Always include:**
        - Cooking methods mentioned (grilled, roasted)
        - Primary proteins (chicken, tofu, lentil)
        - Dietary attributes (high-protein, low-fat)
        - Flavor descriptors (spicy, creamy, aromatic)
        - Cuisine style (indian, thai, italian)
        - Meal context (lunch, party, celebration)
        - Texture descriptors (creamy, crispy, tender)
        - Main components (rice-base, curry-base)
        - Occasions (festival-dish, celebration-meal)
        - Prep style (slow-cooked, marinated, one-pot)

        ---

        ## Immutability Principle

        🔴 **CRITICAL RULE**

        Once a keyword is added to the dictionary, it:
        - ✅ Can be used to map future recipes
        - ✅ Is never modified or renamed
        - ✅ Is never deleted
        - ✅ Keeps the same format forever
        - ❌ Cannot be replaced with a "better" version
        - ❌ Cannot have its meaning changed

        **Why?**: Future recipe mappings depend on keyword stability. If keywords change, historical mappings become incorrect.

        ---

        ## Processing Recipes in Batches

        ```python
        # Batch 1
        existing = ["veg", "non-veg", "lunch"]
        recipes = [recipe_1, recipe_2]
        result_1 = extract(existing, recipes)
        # Returns 30 new keywords

        # Batch 2 - CRITICAL: Update existing keywords
        existing = ["veg", "non-veg", "lunch"] + result_1["new_keywords"]
        recipes = [recipe_3, recipe_4]
        result_2 = extract(existing, recipes)
        # Returns only NEW keywords (not in updated existing list)

        # This maintains immutability across batches
        ```

        ---

        ## Common Examples

        ### Chicken Biryani

        **Category Breakdown**:
        - Dietary (3): non-vegetarian, protein-rich, high-carb
        - Meal Type (6): lunch-friendly, dinner-friendly, festival-dish, celebration-meal, special-occasion, family-gathering
        - Protein (1): chicken
        - Cuisine (3): indian, mughlai-influenced, north-indian
        - Cooking (4): slow-cooked, marinated, layered, spice-blend
        - Flavor (7): spicy, aromatic, fragrant, masala-forward, warming-spice, saffron-forward, cardamom-forward
        - Main Ingredient (3): basmati-rice, yogurt-base, ghee-rich
        - Texture (3): creamy-rice, tender-chicken, fluffy-texture
        - Prep Style (4): marinated, layered, slow-cook, make-ahead
        - Serving (2): party-favorite, family-favorite

        **Total: ~30 keywords**

        ### Quick Vegetable Stir Fry

        **Category Breakdown**:
        - Dietary (5): vegetarian, vegan-friendly, low-calorie, high-fiber, healthy-option
        - Meal Type (4): quick-meal, weeknight-dinner, lunch-preferred, light-meal
        - Cuisine (2): asian-style, chinese-influenced
        - Cooking (3): stir-fried, wok-cooked, high-heat
        - Flavor (4): savory, sesame-forward, garlic-forward, ginger-forward
        - Main Ingredient (3): mixed-vegetables, soy-base, sesame-oil
        - Texture (2): crispy-tender, crunchy-vegetables
        - Prep Style (2): minimal-prep, one-pan
        - Time (2): 15-minute, easy-prep

        **Total: ~25 keywords**

        ---

        ## Python Quick Start

        ```python
        from advanced_keyword_extraction import AdvancedKeywordExtractor

        # Initialize
        extractor = AdvancedKeywordExtractor(your_model, system_prompt)

        # Extract from recipes
        existing = ["veg", "lunch"]
        recipes = [{
            "name": "Chicken Biryani",
            "ingredients": "...",
            "instructions": "...",
            "description": "..."
        }]

        result = extractor.extract_keywords(existing, recipes)

        # Access results
        new_keywords = result["new_keywords"]  # List of 25-35 keywords
        by_recipe = result["extracted_by_recipe"]  # Per-recipe breakdown
        summary = result["summary"]  # Statistics

        print(f"Found {len(new_keywords)} new keywords")
        print(f"Categories: {summary['keywords_by_category']}")
        ```

        ---

        ## Validation Checklist

        Before using extracted keywords:

        - [ ] JSON is valid (can parse without errors)
        - [ ] No existing keywords in output
        - [ ] All keywords are lowercase
        - [ ] All keywords use hyphens (not spaces)
        - [ ] Keywords are 1-3 words max
        - [ ] No recipe names in keywords
        - [ ] No brand names
        - [ ] No generic filler words
        - [ ] 25-35 keywords per recipe
        - [ ] Keywords organized by category
        - [ ] Summary stats are accurate

        ---

        ## Performance Metrics

        | Metric | Target |
        |--------|--------|
        | Keywords per recipe | 25-35 |
        | Category coverage | 8-12 |
        | Quality score | 100% relevant |
        | Immutability | 0% violations |
        | JSON validity | 100% |
        | Batch consistency | Same keywords, same format |

        ---

        ## Temperature Setting

        - **Temperature**: 0.0 (lowest possible)
        - **Reason**: Ensures consistent, deterministic JSON output
        - **Max Tokens**: 3000 (for 25-35 keywords)

        ---

        ## When to Update Existing Keywords

        Update the `existing_keywords` list:
        - ✅ After each batch of recipes
        - ✅ When starting a new batch
        - ✅ Never in between extractions
        - ❌ Don't remove keywords
        - ❌ Don't modify format
        - ❌ Don't replace with "better" versions

        ---

        ## Key Takeaways

        1. **Extract 3 types**: Explicit (direct), Implicit (inferred), Contextual (usage)
        2. **Target 25-35 keywords**: Rich coverage across 12 categories
        3. **Maintain immutability**: Keywords never change once added
        4. **Batch properly**: Update existing keywords between batches
        5. **Validate always**: Check JSON, format, and immutability
        6. **Document categories**: Organized output for downstream use

        ---

        ## Files Reference

        - `advanced_keyword_extraction_prompt.md` - Full system prompt
        - `advanced_keyword_extraction_implementation.md` - Python code and examples
        - `keyword_extraction_quick_reference.md` - This file
    """
    
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
    

    structured_llm = llm.with_structured_output(RecipeKeywords)

    response = structured_llm.invoke(
        [
            SystemMessage(content=RECIPE_KEYWORD_PROMPT),
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
