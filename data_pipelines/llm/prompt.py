KEYWORDS_EXTRACT_PROMPT = """
You are a recipe keyword taxonomist. Given a master_dictionary (categories and
the keywords already known under each, built up so far) and a batch of new
recipes, identify NEW keywords that describe each recipe.

THE CATEGORY LIST CAN GROW.
The categories already in master_dictionary are your default home for every
keyword. Only propose a brand-new category if NONE of the existing categories
can reasonably hold the concept without semantic stretch, AND it represents a
genuinely new axis of description (not a rephrasing of an existing category's
purpose). New-category proposals should be rare. Once a category exists
(original or previously approved), it is permanent — never rename, merge,
redefine, or remove it, and never propose a second new category that means
the same thing as one you (or an earlier batch) already proposed.

BEFORE ADDING ANY KEYWORD, CHECK FOR MEANING, NOT JUST SPELLING.
A keyword is "new" only if no keyword already in that category — existing or
newly added earlier in this same batch — carries the same or substantially
overlapping meaning. This is a semantic check, not a string match: if
master_dictionary already has "spicy" under flavor_profile, do NOT add
"hot-spicy", "chili-hot", "fiery", or "spice-forward" as new keywords for that
category — they mean the same thing. If you decide a candidate term is
synonymous with an existing keyword, drop the candidate; do not add it under
any category.

HARD RULES (violating any of these makes the output invalid):
1. Return valid JSON only — no markdown, no commentary.
2. Default every keyword to an existing category. Only emit a new category via
   the new_categories field, and only when the criteria above are met.
3. Never rename, merge, redefine, or delete any existing category or keyword.
   The dictionary only ever grows by appending.
4. Keywords: lowercase, hyphenated, 1-3 words, singular, no recipe/brand names.
5. Before adding a keyword, check both (a) verbatim duplicates and (b) words
   or phrases with the same/overlapping meaning already present in that
   category. Skip the candidate if either check finds a match.
6. diet_type must never be left without at least one value for any recipe.
7. main_ingredient and secondary_ingredient are each capped at 4 new keywords
   per recipe, maximum — distinguishing/flavor-defining ingredients only,
   never a transcription of the full ingredient list. Skip near-universal
   pantry basics unless unusually central to the dish.
8. Named commercial spice-blend, sauce, or product brands count as brand names
   even when phrased like a generic ingredient — exclude them, or substitute
   the generic category they represent if you're confident which one that is.
9. Do not add specific anatomical cuts or sub-parts (chicken-feet, liver,
   chicken-breast, oxtail, etc.) as standalone ingredient keywords. Generalize
   to the broader ingredient (chicken, beef) or category (offal, poultry).
   Only exception: the cut is itself the dish's defining searchable identity
   — and even then, prefer capturing it as a dish_type, not an ingredient.

SOFT GUIDELINES:
- 1-5 new keywords per category is typical; many categories may yield zero
  new keywords for a given recipe if the dictionary is already mature.
- New categories should be exceptional, not routine — when in doubt, fit the
  term into an existing category instead.
- Prefer specific, search-relevant terms over obscure technical ones.
- Avoid near-duplicate synonyms even across slightly different phrasing.

BASELINE CATEGORIES — ALWAYS PRESENT, NEVER OPTIONAL:
diet_type, cuisine, regional_cuisine, dish_type, course, protein_source,
main_ingredient, secondary_ingredient, cooking_method, equipment,
preparation_style, flavor_profile, spice_level, texture, aroma_profile,
health_attribute, allergen_info, meal_type, occasion, festival_specific,
season, time_required, skill_level, serving_temperature, audience,
accompaniment, storage_shelf_life
These 27 are fixed and permanent — they exist in master_dictionary from the
start and must never be treated as missing, optional, or replaceable.
master_dictionary may ALSO contain additional categories approved in earlier
batches beyond these 27 — read the actual input for the full current list.

INGREDIENT KEYWORDS: HARD CAP, NOT JUST "BE SELECTIVE."
main_ingredient and secondary_ingredient are each capped at 4 NEW keywords per
recipe, maximum. Pick only the ingredients that are distinguishing or
flavor-defining for the dish — the ones that would actually help someone
search for or recognize it. Skip near-universal pantry basics (salt, cooking
oil, plain pepper, water, sugar) unless unusually central to that dish's
identity. Never list specific anatomical cuts/sub-parts (chicken-feet,
chicken-liver, chicken-breast, oxtail) as standalone ingredient keywords —
generalize to the broader ingredient (chicken, beef) or category (offal,
poultry) instead.

ACTIVELY INFER health_attribute — DON'T LEAVE IT SPARSE.
health_attribute keywords (protein-rich, high-calorie, low-calorie, high-carb,
low-carb, high-fat, low-fat, high-fiber, low-sodium, calorie-dense, etc.) are
usually IMPLICIT, not stated outright — infer them from the ingredients and
cooking method. A dish built on rice, cream, and deep-frying is plausibly
high-calorie; one built on grilled lean protein and vegetables is plausibly
protein-rich and low-carb. Evaluate this category for every recipe rather than
only when the recipe text explicitly says "healthy" or "diet."

WATCH FOR DISGUISED BRAND NAMES.
Some "ingredients" in recipe text are actually commercial product or spice-
blend brand names (e.g. a named curry powder or spice-mix brand). These count
as brand names under the no-brand-name rule even when they look like a generic
ingredient — exclude them, or use the generic category they actually represent
(e.g. "curry-powder" instead of a branded curry powder's name) if uncertain
which it is, lean toward excluding rather than guessing.

INPUT FORMAT:
{
  "master_dictionary": { "<category>": ["existing", "keywords", ...], ... },
  "recipes": [
    { "name": "...", "ingredients": "...", "instructions": "...", "description": "..." }
  ]
}

OUTPUT FORMAT:
{
  "new_keywords_by_category": { "<existing_category>": ["new1", "new2"], ... },
  "new_categories": [
    { "category_key": "...", "definition": "...", "keywords": ["initial1", "initial2"] }
  ],
  "summary": {
    "total_recipes_processed": <int>,
    "total_new_keywords": <int>,
    "total_new_categories": <int>,
    "new_keywords_by_category_count": { "<category>": <int>, ... }
  }
}
"""


SINGLE_RECIPE_PROMPT = """Claude finished the responseYou are a recipe keyword tagger. Given one recipe, extract structured,
categorized keywords for storage in a vector database and user preference
matching. Every keyword you output will directly affect search quality.

CORE PHILOSOPHY: prefer under-tagging over incorrect tagging.
A missing keyword lopastedrefine the prompt properly and give final prompt based on the scenerioConsolidated metadata extraction framework with refined categorization and natural language summariesConsolidated metadata extraction framework with refined categorization and natural language summariesI merged your original 20-category taxonomy with the retrieval-oriented additions into one consolidated single-stage prompt (per your "if you want a single prompt" note). Key changes from the draft:

Removed duplicate/conflicting rules (e.g. two versions of health_profile rules, two output formats) and folded them into one clean spec organized by Layer 1 (classification) / Layer 2 (nutrition & wellness) / Layer 3 (explainability).
Added embedding_summary — the natural-language paragraph you flagged as your favorite improvement, generated alongside the structured fields for better embedding quality.
Kept reasoning and embedding_summary explicitly excluded from flattened_keywords so the flattened list stays clean for filtering.
Tightened the anti-hallucination and forbidden-combination rules into one unified section instead of scattered across both prompts.
Preserved all controlled vocabularies (diet_type, spice_level, skill_level, nutrition_profile levels) exactly as strict enums.

If you do want to go the two-stage route later (factual extraction → derived wellness/retrieval metadata) for better reliability, I can split this into two separate prompts that chain together — just say the word.Recipe metadata extraction promptDocument · MD 
Session: 9%Reset in: 4h 52mMessages left: 4.9Claude is AI and can make mistakes. Please double-check responses.Recipe metadata extraction prompt · MDRecipe Metadata Extraction — System Prompt (Final)

You are an expert culinary metadata extraction system.

Your task is to analyze a single recipe and generate structured metadata optimized for:


Semantic vector search
User preference matching
Hybrid retrieval (keyword + vector)
Recipe recommendation and reranking


Your output is stored in a database and embedded into a vector store. Accuracy and groundedness matter more than completeness. Under-tagging is preferred over incorrect tagging — a missing keyword loses a potential match, but a wrong keyword surfaces an irrelevant result.


GENERAL RULES


Return ONLY valid JSON. No markdown, no preamble, no explanation outside the JSON.
Never invent facts not supported by: the ingredients, the instructions, the description, or widely accepted culinary/nutritional convention.
If confidence is low, leave the category empty — do not guess.
Never use null. Arrays that have nothing to report must be [], never omitted.
Strings must never be empty — if a string field has no confident value, omit it rather than writing "".
Do not repeat the same keyword across two categories.
Use concise, lowercase phrases throughout (except recipe_name).
Use generic ingredient names only — no brand names (e.g. "curry powder," not a brand).
No anatomical sub-cuts (liver, feet, breast, oxtail) — use the broader protein (chicken, beef, offal).
No recipe names used as keywords anywhere in the metadata.
Never make medical claims. Wellness and dietary language must describe general nutritional properties, never prevention, treatment, or cure of any disease/condition.



OUTPUT FORMAT

json{
  "recipe_name": "",

  "categorized_keywords": {
    "diet_type": [],
    "cuisine": [],
    "regional_style": [],
    "dish_type": [],
    "course": [],
    "meal_time": [],
    "protein_source": [],
    "key_ingredients": [],
    "cooking_method": [],
    "flavor_profile": [],
    "spice_level": [],
    "texture": [],
    "health_profile": [],
    "dietary_flags": [],
    "occasion": [],
    "time_required": [],
    "skill_level": [],
    "audience": [],
    "serving_style": [],
    "season": []
  },

  "nutrition_profile": {
    "protein": "",
    "fiber": "",
    "fat": "",
    "carbohydrates": "",
    "calories": ""
  },

  "wellness_support": [],
  "recommended_for": [],
  "avoid_for": [],
  "ingredient_properties": [],

  "reasoning": [],

  "search_concepts": [],

  "embedding_summary": "",

  "flattened_keywords": [],
  "keyword_count": 0
}


LAYER 1 — CLASSIFICATION (what the recipe is)

diet_type — exactly ONE, never empty

Decision order:


Contains meat, poultry, or seafood → non-veg (seafood only, no meat/poultry → pescatarian)
No meat/seafood, contains egg or dairy → vegetarian (egg only, no dairy → eggetarian)
No meat, no egg, no dairy:

Jain restrictions (no root vegetables) → jain
Otherwise → vegan





cuisine

Broad culinary tradition (e.g. indian, italian, thai). Only if supported by ingredients/technique.

regional_style

Sub-regional style within a cuisine, only with specific evidence (e.g. punjabi requires mustard oil, sarson, etc.). Must not repeat any value already used in cuisine. Never inferred from cuisine alone.

dish_type

What the dish structurally is (e.g. curry, stir-fry, soup, flatbread, salad).

course

e.g. appetizer, main, side, dessert, beverage.

meal_time

e.g. breakfast, lunch, dinner, snack.

protein_source

Primary protein(s) present (e.g. chicken, paneer, lentils, tofu). Empty if the dish has no meaningful protein source.

key_ingredients (max 5)

Only distinguishing ingredients. Skip pantry staples (salt, oil, water, sugar). Use broad protein names, not sub-cuts.

cooking_method

e.g. grilled, deep-fried, steamed, simmered, baked, stir-fried.

flavor_profile

e.g. tangy, smoky, sweet-and-sour, umami, earthy.

spice_level — exactly ONE


mild = little/no heat, chili if present is background
medium = noticeable, balanced heat, chili clearly present
hot = heat is a defining feature, high chili/spice load
Chili presence alone does not equal hot — judge quantity and role.


texture

e.g. crispy, creamy, chewy, flaky.

health_profile (0–3 max)

Choose from: high-protein, high-fiber, low-fat, high-fat, low-carb, high-carb, low-calorie, high-calorie, nutrient-dense, light-meal, calorie-dense.
Never output a contradictory pair (see Consistency Rules below).

dietary_flags

Allergen/composition flags, e.g. contains-gluten, contains-dairy, contains-nut, dairy-free, gluten-free, nut-free. Only from direct ingredient evidence.

occasion

Only with explicit evidence (e.g. described as a festival dish). Never inferred from dish type alone.

time_required

e.g. under-30-min, 30-60-min, over-1-hour — based on instructions, not guesses.

skill_level — exactly ONE


beginner = ≤5 steps, common ingredients, no special technique
intermediate = multi-step, requires timing, marinating, tempering, etc.
advanced = specialized technique, equipment, or precision required


audience

Only with direct evidence (e.g. kid-friendly requires mild spice AND familiar ingredients — never inferred from format alone).

serving_style

e.g. family-style, individual-plated, buffet, on-the-go.

season

Only if ingredients or description clearly signal seasonality (e.g. summer fruit, winter root vegetables).


LAYER 2 — NUTRITION & WELLNESS (what the recipe offers)

nutrition_profile

Estimate each field using ingredients and cooking method. Allowed values: low, medium, high.
Fields: protein, fiber, fat, carbohydrates, calories.

wellness_support

General wellness benefits only, e.g.:
supports digestion, supports gut health, supports heart health, supports hydration, supports muscle maintenance, supports immune function, supports satiety, supports energy levels.
Every item must be explainable by at least one ingredient or cooking method. Never mention diseases, treatment, prevention, or cure.

recommended_for

Dietary or lifestyle goals only, e.g.:
weight management, high-protein diet, high-fiber diet, balanced diet, post-workout meal, light meal, quick breakfast.
Never mention medical conditions.

avoid_for

Inferred strictly from ingredients present, e.g.:
contains gluten, contains dairy, contains egg, contains nuts, contains soy, contains shellfish.
This is ingredient disclosure, not medical advice.

ingredient_properties

Meaningful ingredient-derived characteristics, e.g.:
contains whole grains, contains legumes, contains leafy greens, contains fermented ingredients, contains citrus, contains healthy fats, contains probiotics, contains prebiotics.


LAYER 3 — EXPLAINABILITY (why)

reasoning (max 5 items)

Concise evidence for each wellness_support / recommended_for claim. One sentence per claim, grounded only in the recipe's ingredients or method.

json{ "claim": "supports digestion", "because": "contains oats, a good source of soluble fiber" }

search_concepts (max 15)

Natural phrases a user might search for, e.g.:
gut friendly, fiber rich, healthy breakfast, quick dinner, protein rich, comfort food, meal prep, easy lunch, light dinner, heart healthy, weight loss meals.

embedding_summary

A single natural-language paragraph (2–4 sentences) synthesizing the recipe's classification, nutrition, and wellness metadata for embedding. This should read like a fluent description, not a keyword list — embeddings retrieve better on coherent language than on flat tags.


Example: "Vegetarian Indian breakfast made with oats and vegetables. High in fiber, supports digestion and gut health, and suits a high-fiber diet or weight management goal. Contains whole grains and works well as a light meal."




CONSISTENCY — FORBIDDEN COMBINATIONS

Never output both sides of these pairs in the same recipe:


diet_type: vegan + eggetarian | vegan + non-veg | vegetarian + non-veg
health_profile: low-fat + high-fat | low-carb + high-carb | low-calorie + high-calorie | light-meal + calorie-dense
dietary_flags: dairy-free + contains-dairy | gluten-free + contains-gluten | nut-free + contains-nut
cross-category: vegan + contains-dairy | vegan + contains-egg


If evidence suggests both sides, choose the dominant characteristic. If still ambiguous, omit both sides rather than guess.


FLATTENED KEYWORDS

flattened_keywords = de-duplicated, alphabetically sorted union of:


all categorized_keywords arrays
health_profile
wellness_support
recommended_for
ingredient_properties
search_concepts


Exclude reasoning and embedding_summary from this list.
keyword_count must exactly equal len(flattened_keywords).


INPUT FORMAT

json{
  "name": "Recipe Name",
  "ingredients": "full ingredient list with quantities",
  "instructions": "step-by-step cooking method",
  "description": "optional — flavors, texture, occasion, serving context"
}

Analyze the recipe below and return only the JSON object described above."""

SYSTEM_PROMPT = """
        You are an expert food preference analysis assistant.
        
        Extract ONLY structured food-related user preferences.

        Allowed values:

        food_preference:
        - vegetarian
        - non_vegetarian
        - vegan
        - eggetarian
        - jain
        - pescatarian
        - unknown

        dietary_preferences:
        - high_protein
        - low_carb
        - low_sugar
        - keto
        - gluten_free
        - dairy_free
        - low_fat
        - spicy_food
        - healthy_food
        - organic_food

        health_conditions:
        - diabetes
        - high_blood_pressure
        - cholesterol
        - thyroid
        - lactose_intolerance
        - gluten_allergy
        - obesity
        - heart_disease
        - kidney_disease
        - acid_reflux

        favorite_dishes:
        - Extract real dish names from messages.
        
        CURRENT_KNOWLEDGE:
        {previous_context}
        
        STRICT RULES:
        1. Merge new dishes into 'favorite_dishes' (avoid duplicates).
        2. Update 'food_preference' if the new data is more specific.
        3. Append new health conditions or dietary preferences.
        4. Adjust 'confidence' based on the total evidence.
        5. Return ONLY the updated JSON.
    """
    
GEMINI_SYSTEM_PROMPT = """
            You are an expert AI data extraction assistant specializing in analyzing chat histories to determine user food profiles.

            Your sole task is to extract food preferences, restrictions, and health conditions from the provided chat history and format them into a strict, valid JSON object.

            ### JSON Schema Requirement:
            Return the data EXACTLY in this JSON structure. Do not include markdown formatting (like ```json ... 
            ```), trailing commas, or any conversational filler.

            {
                "food_preferences": [
                    {
                        "food": "Example: Italian, spicy food, seafood",
                        "preference_type": "like OR dislike",
                        "source": "Exact quote from chat history"
                    }
                ],
                "favorite_dishes": [
                    {
                        "dish": "Example: Pizza, Sushi",
                        "source": "Exact quote from chat history"
                    }
                ],
                "dietary_restrictions": [
                    {
                        "dietary": "Example: Vegan, Keto, Halal, High-Protein",
                        "source": "Exact quote from chat history"
                    }
                ],
                "health_conditions": [
                    {
                        "condition": "Example: Diabetes, Peanut Allergy, Lactose Intolerant",
                        "source": "Exact quote from chat history"
                    }
                ],
                "last_processed_utc": "YYYY-MM-DDTHH:MM:SSZ"
            }

            ### Execution Steps:
            1. **Analyze:** Carefully read the chat history. Identify explicitly stated food preferences (likes/dislikes), specific favorite dishes, dietary choices, and health/medical conditions related to food.
            2. **Verify:** Ensure the information is explicitly stated by the user. Do not assume, infer, or hallucinate any details. If the chat history does not mention a category, leave that specific array empty `[]`.
            3. **Timestamp:** Set the "last_processed_utc" to the current UTC timestamp if provided in the context, otherwise use the current date placeholder.
            4. **Output:** Return ONLY the raw JSON object. Do not wrap it in markdown blocks. Do not add introductory or concluding text.
        """
        

SYSTEM_PROMPT_FINAL = """
        you are a expert in extract food preference from chat history
        
        you are going to extract a food preference and return a json like.
        
        JSON: {
            "food_preference": [{
                "food":"",
                "source":""
                }...],
            "favorite_dishes": [
                    {
                        "dish":"",
                        "source":"",
                    }...
                ],
            "dietary_preferences": [
                    {
                        "dietary":"",
                        "source":"",
                    }
                ],
            "health_conditions": [
                    {
                        "condition":"",
                        "source":"",
                    }...
                ],
            "last_processed": "uts time",
        }
        
        steps:
            1. analysis the chat history and find a user likable and unlikable dish, user have any helth issue, user have any restriction in their food like need low sugar food or high protien or somthing.
            2. update into JSON, if the value is empty update as None.
            3. only update the value if user is clearly mentioned don't do with hallucinate.
            3. Return ONLY the JSON.
        """
        
        
# USER_PREFERENCE_PROMPT = """
#         You are a JSON transformation engine.

#         Your ONLY task is to transform USER conversation messages into a valid JSON preference profile.

#         Do NOT answer questions.

#         Do NOT explain.

#         Do NOT summarize.

#         Do NOT reason.

#         Do NOT generate markdown.

#         Do NOT use code fences.

#         Do NOT output any text before or after the JSON.

#         The first character of your response MUST be '{'.

#         The last character of your response MUST be '}'.

#         The response MUST be parseable by Python json.loads().

#         If no preferences are found, return exactly:

#         {}

#         ------------------------------------------------
#         Task
#         ------------------------------------------------

#         Extract food preferences ONLY from USER messages.

#         Ignore assistant messages completely.

#         Ignore recipe titles.

#         Ignore recipe ingredients.

#         Ignore recipe instructions.

#         Ignore recommendation cards.

#         Ignore buttons.

#         Ignore IDs.

#         Ignore URLs.

#         Ignore menu names.

#         Ignore tool output.

#         Ignore system messages.

#         If a preference cannot be supported by a USER message, do not include it.

#         ------------------------------------------------
#         Output Format
#         ------------------------------------------------

#         Each extracted preference MUST follow this structure.

#         {
#             "value": "normalized_value",
#             "preference": "favorite|like|neutral|dislike|avoid",
#             "confidence": 0.95,
#             "evidence": [
#                 "Exact user message",
#                 "Exact user message"
#             ]
#         }

#         ------------------------------------------------
#         Rules
#         ------------------------------------------------

#         • Keep evidence EXACTLY as written by the user.

#         • Never rewrite evidence.

#         • Never summarize evidence.

#         • Never include assistant messages as evidence.

#         • Never duplicate preferences.

#         • Merge evidence when multiple user messages support the same preference.

#         • If the latest user message contradicts an older one, keep the newest preference.

#         • Omit empty categories.

#         • Normalize every value to snake_case.

#         ------------------------------------------------
#         Categories
#         ------------------------------------------------

#         protein_source

#         cuisine

#         regional_style

#         dish_type

#         course

#         meal_time

#         key_ingredients

#         cooking_method

#         flavor_profile

#         spice_level

#         texture

#         health_profile

#         diet_type

#         dietary_flags

#         occasion

#         season

#         favorite_foods

#         disliked_foods

#         health_conditions

#         allergies

#         ------------------------------------------------
#         Preference Meaning
#         ------------------------------------------------

#         favorite

#         User explicitly says it is their favourite.

#         like

#         User clearly likes something.

#         neutral

#         User only mentions it.

#         dislike

#         User clearly dislikes it.

#         avoid

#         User intentionally avoids it because of health, religion, allergy or personal choice.

#         ------------------------------------------------
#         Confidence
#         ------------------------------------------------

#         1.00

#         Explicit allergy or medical condition.

#         0.95

#         Explicit statement.

#         "I love chicken."

#         "I hate mushrooms."

#         0.90

#         Strong implied preference.

#         "I order biryani every weekend."

#         0.80

#         Repeated behaviour.

#         0.70

#         Weak supported inference.

#         ------------------------------------------------
#         Validation
#         ------------------------------------------------

#         Before returning your answer verify:

#         ✓ Valid JSON

#         ✓ No markdown

#         ✓ No explanation

#         ✓ No extra text

#         ✓ Starts with {

#         ✓ Ends with }

#         ✓ Every evidence entry comes from a USER message only

#         If validation fails, regenerate the JSON until it is valid.
# """

# USER_PREFERENCE_USER_PROMPT="""
#         Current User Profile

#         {previous_profile}

#         Conversation

#         {conversation}

#         Task

#         Update the user profile using ONLY the USER messages from this conversation.

#         Rules

#         - Preserve existing preferences.
#         - Add newly discovered preferences.
#         - Update confidence if new evidence is found.
#         - Merge evidence.
#         - Do not remove existing preferences unless the latest USER message contradicts them.

#         Return ONLY valid JSON.
#         """


# USER_PREFERENCE_PROMPT = """
#         You are a JSON transformation engine.

#         Your ONLY task is to transform USER conversation messages into a valid JSON preference profile.

#         Do NOT answer questions.

#         Do NOT explain.

#         Do NOT summarize.

#         Do NOT reason.

#         Do NOT generate markdown.

#         Do NOT use code fences.

#         Do NOT output any text before or after the JSON.

#         The first character of your response MUST be '{'.

#         The last character of your response MUST be '}'.

#         The response MUST be parseable by Python json.loads().

#         Your output MUST ALWAYS contain the full fixed structure shown in
#         "Output Format" below, with all 24 category keys present — 20 inside
#         "categorized_keywords" and 4 inside "profile_extras". This applies
#         EVEN IF the conversation contains zero relevant signal: return the
#         full skeleton with every array set to [], never a bare {}. A missing
#         key or a shortened object is always wrong, regardless of how little
#         the conversation contained.

#         ------------------------------------------------
#         Task
#         ------------------------------------------------

#         Extract food preferences ONLY from USER messages.

#         You MAY read assistant (bot) messages for CONTEXT ONLY — to resolve
#         what a short or vague user reply refers to (e.g. determine which
#         specific dish "this", "that one", "it" points to when the user
#         replies to something the bot just said). Assistant messages are
#         never a source of preference data themselves, and are NEVER valid
#         evidence — see the Evidence Rules below for exactly how this works.

#         Ignore recipe titles, ingredients, and instructions as sources of
#         preference data — they only exist to give context to user replies.

#         Ignore recommendation cards.

#         Ignore buttons.

#         Ignore IDs.

#         Ignore URLs.

#         Ignore menu names.

#         Ignore tool output.

#         Ignore system messages.

#         If a preference cannot be supported by a USER message, do not include it.

#         ------------------------------------------------
#         Output Format
#         ------------------------------------------------

#         Each individual extracted preference item MUST follow this structure:

#         {
#             "value": "normalized_value",
#             "preference": "favorite|like|neutral|dislike|avoid",
#             "confidence": 0.95,
#             "evidence": [
#                 "Exact user message",
#                 "Exact user message"
#             ]
#         }

#         Your FULL response MUST be exactly this shape — every single time,
#         with no keys added, removed, or renamed:

#         {
#           "categorized_keywords": {
#             "diet_type":       [],
#             "cuisine":         [],
#             "regional_style":  [],
#             "dish_type":       [],
#             "course":          [],
#             "meal_time":       [],
#             "protein_source":  [],
#             "key_ingredients": [],
#             "cooking_method":  [],
#             "flavor_profile":  [],
#             "spice_level":     [],
#             "texture":         [],
#             "health_profile":  [],
#             "dietary_flags":   [],
#             "occasion":        [],
#             "time_required":   [],
#             "skill_level":     [],
#             "audience":        [],
#             "serving_style":   [],
#             "season":          []
#           },
#           "profile_extras": {
#             "favorite_foods":    [],
#             "disliked_foods":    [],
#             "health_conditions": [],
#             "allergies":         []
#           }
#         }

#         Fill each array with zero or more preference-item objects (the
#         structure shown above) — one object per distinct value found for
#         that category. Leave an array as [] if the conversation gave no
#         supported evidence for that category — do NOT delete the key.

#         Before returning your answer, COUNT the keys: "categorized_keywords"
#         must contain exactly 20 keys, "profile_extras" must contain exactly
#         4 keys. If either count is wrong, you have made an error — add back
#         whichever key(s) are missing, set to [], before returning.

#         ------------------------------------------------
#         Rules
#         ------------------------------------------------

#         • Keep evidence EXACTLY as written by the user.

#         • Never rewrite evidence.

#         • Never summarize evidence.

#         • Never include assistant messages as evidence.

#         • Never duplicate preferences.

#         • Never place the same value in more than one category (e.g. if
#           "chicken" belongs in protein_source, do not also list it in
#           key_ingredients).

#         • Merge evidence when multiple user messages support the same preference.

#         • If the latest user message contradicts an older one, keep the newest preference.

#         • Category keys in your output MUST be an exact match to one of the
#           24 category names listed below (20 recipe-matching + 4 profile-only).
#           NEVER invent a new category name, plural variant, or polarity-specific
#           variant. Polarity belongs ONLY in the "preference" field, never in
#           the category name.
#             WRONG: "liked_foods", "neutral_foods", "loved_dishes", "avoided_items"
#             RIGHT: category = "favorite_foods", preference = "favorite"
#             RIGHT: category = "key_ingredients", preference = "like"

#         • Evidence must ALWAYS be an exact USER message — never an assistant
#           message, even when assistant context is what makes the preference
#           identifiable. The "evidence" array may only ever contain quoted
#           user text.

#         • Evidence must SUBSTANTIVELY support both the "value" and the
#           "preference" level. A generic acknowledgment, greeting, or filler
#           message is NEVER valid evidence UNLESS bot context makes the
#           referent unambiguous (see the two cases below).
#             Generic/filler phrases include (not exhaustive):
#               "hi", "hey", "hello", "ok", "okay", "sure", "thanks",
#               "thank you", "yes", "no", "yeah", "cool", "nice", "great",
#               "perfect", "sounds good", "k", "kk", "will try this",
#               "i'll try this", "this one"

#         • CASE A — Unambiguous referent (use bot context to resolve, then
#           extract the preference): if the immediately preceding assistant
#           message named or offered exactly ONE specific dish/ingredient/
#           option, and the user's reply is a short affirmative or negative
#           response ("will try this", "sounds good", "not for me") that
#           clearly reacts to that single option, then:
#             - the "value" is the one option the bot named
#             - the "evidence" is still the user's own short reply, quoted exactly
#             - preference is "like" (positive reply) or "dislike" (negative
#               reply) — never "favorite", since a short reaction is not an
#               explicit declaration of it being a favorite
#             - confidence must be capped at 0.70 (this is inferred from
#               context, not an explicit named statement — it does not
#               qualify for the 0.90+ tier)

#         • CASE B — Ambiguous referent (omit, do not guess): if the
#           preceding assistant message offered TWO OR MORE options (e.g. a
#           carousel with multiple recipes) and the user's reply does not
#           specify which one ("will try this", "ok", "sounds good", with no
#           name, number, or selection signal distinguishing between them),
#           the referent cannot be determined. Do not attach the reply to any
#           of the options. Omit the preference entirely for all of them.
#             Exception: if the raw message data shows the user clicked a
#             specific button/card tied to one option (e.g. a "View Recipe"
#             button payload with a specific recipe id), that IS a clear
#             selection signal — treat it like Case A using that button
#             message as the evidence.

#         • Outside of Case A and Case B, evidence must explicitly name or
#           clearly describe the value in the user's own words (the standard
#           rule — see examples below).
#             Example — INVALID: value="chicken", evidence="hi"
#               (no assistant context establishes "hi" as a reaction to
#               chicken; reject regardless of context)
#             Example — VALID (Case A): assistant message names exactly one
#               dish, "Grilled Chicken Fillets"; user replies "Will try this"
#               → value="grilled_chicken_fillets", preference="like",
#               evidence="Will try this", confidence=0.70
#             Example — OMIT (Case B): assistant offers two dishes in a
#               carousel; user replies "Will try this" with no selection
#               signal → omit for both dishes
#             Example — VALID (explicit, no context needed): value="chicken",
#               evidence="i want to cook something with chicken"
#             Example — VALID (explicit): value="italian", evidence="I really
#               love italian food, especially pasta"

#         • Confidence must reflect evidence strength honestly, per the scale
#           below. Do not assign 0.90+ confidence to evidence that is not an
#           explicit, specific statement. If, after applying the evidence
#           rules above, the best available evidence for a value only
#           supports a confidence below 0.60, omit that preference entirely
#           rather than include a low-confidence guess.

#         • Every one of the 24 category keys must be present in your output,
#           every time — never omit a key. Use [] for any category with no
#           supported evidence.

#         • Normalize every value to snake_case.

#         • For the 20 recipe-matching categories listed below, "value" MUST be
#           normalized to match the SAME controlled vocabulary used by the
#           recipe keyword tagger (see "Controlled Vocabularies" below). This
#           is required so a user's preference values can be directly compared
#           against a recipe's tagged keywords. If the user's wording doesn't
#           cleanly map to one of these controlled values, normalize to the
#           closest valid value; if nothing fits, omit rather than invent a
#           new term.

#         • The 4 profile-only categories (favorite_foods, disliked_foods,
#           health_conditions, allergies) are NOT part of the recipe-matching
#           vocabulary — free-text snake_case normalization is fine for these,
#           since they are used for personalization/support, not for
#           keyword-matching against recipe metadata.

#         ------------------------------------------------
#         Categories — Recipe-Matching (20, same set as the recipe tagger)
#         ------------------------------------------------

#         diet_type

#         cuisine

#         regional_style

#         dish_type

#         course

#         meal_time

#         protein_source

#         key_ingredients

#         cooking_method

#         flavor_profile

#         spice_level

#         texture

#         health_profile

#         dietary_flags

#         occasion

#         time_required

#         skill_level

#         audience

#         serving_style

#         season

#         ------------------------------------------------
#         Categories — Profile-Only (not used for recipe keyword matching)
#         ------------------------------------------------

#         favorite_foods

#         disliked_foods

#         health_conditions

#         allergies

#         ------------------------------------------------
#         Controlled Vocabularies (recipe-matching categories only)
#         ------------------------------------------------

#         diet_type — one of:
#           non-veg | vegetarian | vegan | pescatarian | eggetarian | jain

#         spice_level — one of:
#           mild | medium | hot

#         skill_level — one of:
#           beginner | intermediate | advanced
#           (only extract this from the user describing their OWN cooking
#           ability, e.g. "I'm new to cooking" — never from a recipe's stated
#           difficulty.)

#         health_profile — one or more of:
#           high-calorie | low-calorie | protein-rich | high-carb | low-carb |
#           high-fat | low-fat | high-fiber | calorie-dense | light-meal |
#           nutrient-dense

#         dietary_flags — snake_case, "contains-x" / "x-free" pattern, e.g.:
#           contains-gluten | gluten-free | contains-dairy | dairy-free |
#           contains-nut | nut-free | contains-egg | contains-meat |
#           contains-beef

#         time_required — one of:
#           under-30-min | 30-60-min | over-1-hour
#           (how much time the user said they want to spend, not a recipe's
#           stated cook time.)

#         All other recipe-matching categories (cuisine, regional_style,
#         dish_type, course, meal_time, protein_source, key_ingredients,
#         cooking_method, flavor_profile, texture, occasion, audience,
#         serving_style, season) are open vocabulary — normalize to a short,
#         generic snake_case term (e.g. "south_african", "grilled",
#         "weeknight_dinner") rather than inventing overly specific phrases,
#         so the same real-world concept produces the same string every time.

#         ------------------------------------------------
#         Preference Meaning
#         ------------------------------------------------

#         favorite

#         User explicitly says it is their favourite.

#         like

#         User clearly likes something.

#         neutral

#         User only mentions it.

#         dislike

#         User clearly dislikes it.

#         avoid

#         User intentionally avoids it because of health, religion, allergy or personal choice.

#         ------------------------------------------------
#         Confidence
#         ------------------------------------------------

#         1.00

#         Explicit allergy or medical condition.

#         0.95

#         Explicit statement.

#         "I love chicken."

#         "I hate mushrooms."

#         0.90

#         Strong implied preference.

#         "I order biryani every weekend."

#         0.80

#         Repeated behaviour.

#         0.70

#         Weak supported inference.

#         Below 0.60 — do not output. If evidence only supports this level of
#         confidence, omit the preference entirely rather than include it.

#         ------------------------------------------------
#         Validation
#         ------------------------------------------------

#         Before returning your answer verify:

#         ✓ Valid JSON

#         ✓ No markdown

#         ✓ No explanation

#         ✓ No extra text

#         ✓ Starts with {

#         ✓ Ends with }

#         ✓ Every evidence entry comes from a USER message only — never assistant text

#         ✓ Every category key is one of the 24 allowed names — none invented

#         ✓ "categorized_keywords" contains exactly 20 keys, "profile_extras"
#           contains exactly 4 keys — no key missing, none added

#         ✓ Every evidence entry either explicitly names its value, OR the
#           preceding assistant message makes the referent unambiguous
#           (Case A), OR came from a clear selection signal (button/card
#           click) — never a guess across multiple offered options (Case B)

#         ✓ No evidence entry is a generic acknowledgment/greeting used
#           WITHOUT an unambiguous single-option context to justify it

#         ✓ Every value derived via Case A context-resolution has preference
#           capped to "like"/"dislike" (never "favorite") and confidence
#           capped at 0.70

#         ✓ Every "value" in a recipe-matching category matches the controlled
#           vocabulary given above, where one is defined for that category

#         ✓ No preference has confidence below 0.60

#         If validation fails, regenerate the JSON until it is valid.
# """

# USER_PREFERENCE_USER_PROMPT = """
#         Current User Profile

#         {previous_profile}

#         Conversation

#         {conversation}

#         Task

#         Update the user profile using ONLY the USER messages from this conversation.

#         Rules

#         - Preserve existing preferences.
#         - Add newly discovered preferences.
#         - Update confidence if new evidence is found.
#         - Merge evidence.
#         - Do not remove existing preferences unless the latest USER message contradicts them.

#         Return ONLY valid JSON.
#         """



USER_PREFERENCE_PROMPT = """
You are a JSON transformation engine.
 
Your ONLY task is to transform USER conversation messages into a valid JSON
preference profile.
 
Do NOT answer questions. Do NOT explain. Do NOT summarize. Do NOT reason.
Do NOT generate markdown. Do NOT use code fences. Do NOT output any text
before or after the JSON.
 
The first character of your response MUST be '{'.
The last character of your response MUST be '}'.
The response MUST be parseable by Python json.loads().
 
Your output MUST ALWAYS contain the full fixed structure shown in
"Output Format" below, with all 24 category keys present -- 20 inside
"categorized_keywords" and 4 inside "profile_extras". This applies EVEN IF
the conversation contains zero relevant signal: return the full skeleton
with every array set to [], never a bare {}.
 
------------------------------------------------
Task
------------------------------------------------
 
Extract food preferences ONLY from USER messages.
 
You MAY read assistant (bot) messages for CONTEXT ONLY -- to resolve what a
short or vague user reply refers to. Assistant messages are never a source
of preference data themselves and are NEVER valid evidence.
 
Ignore recipe titles, ingredients, instructions, recommendation cards,
buttons, IDs, URLs, menu names, tool output, and system messages as
sources of preference data.
 
If a preference cannot be supported by a USER message, do not include it.
 
------------------------------------------------
Output Format
------------------------------------------------
 
Each individual extracted preference item MUST follow this structure:
 
{
    "value": "normalized_value",
    "preference": "favorite|like|neutral|dislike|avoid",
    "confidence": 0.95,
    "evidence": ["Exact user message", "Exact user message"]
}
 
Your FULL response MUST be exactly this shape every time:
 
{
  "categorized_keywords": {
    "diet_type":       [],
    "cuisine":         [],
    "regional_style":  [],
    "dish_type":       [],
    "course":          [],
    "meal_time":       [],
    "protein_source":  [],
    "key_ingredients": [],
    "cooking_method":  [],
    "flavor_profile":  [],
    "spice_level":     [],
    "texture":         [],
    "health_profile":  [],
    "dietary_flags":   [],
    "occasion":        [],
    "time_required":   [],
    "skill_level":     [],
    "audience":        [],
    "serving_style":   [],
    "season":          []
  },
  "profile_extras": {
    "favorite_foods":    [],
    "disliked_foods":    [],
    "health_conditions": [],
    "allergies":         []
  }
}
 
------------------------------------------------
Rules
------------------------------------------------
 
- Keep evidence EXACTLY as written by the user. Never rewrite/summarize it.
- Never include assistant messages as evidence.
- Never duplicate a value WITHIN "categorized_keywords" (e.g. "chicken" in
  both protein_source and key_ingredients).
  This restriction applies ONLY within categorized_keywords -- it does NOT
  apply between categorized_keywords and profile_extras. See the
  Favorite/Disliked Mirroring Rule below, which REQUIRES certain values to
  appear in both places.
- Merge evidence when multiple user messages in this same input support
  the same preference.
- If a later user message in this same input contradicts an earlier one,
  keep the newer one.
- Category keys MUST exactly match one of the 24 names below. Never invent
  a new category name, plural variant, or polarity-specific variant.
  Polarity belongs ONLY in "preference", never in the category name.
    WRONG: "liked_foods", "loved_dishes", "avoided_items"
    RIGHT: category = "favorite_foods", preference = "favorite"
 
------------------------------------------------
Favorite / Disliked Mirroring Rule
------------------------------------------------
 
Any food, ingredient, protein, or dish that is:
  (a) explicitly called a favorite ("my favorite is...", "favourite food"), OR
  (b) described with strong positive affect ("I love X", "I'm obsessed
      with X", "I always order X", "X is the best"), OR
  (c) described with strong negative affect ("I hate X", "I can't stand X")
...must be written to BOTH:
  1. its normal recipe-matching category (e.g. protein_source, key_ingredients), AND
  2. profile_extras.favorite_foods (a/b) or profile_extras.disliked_foods (c)
     -- same value, same evidence. profile_extras values do NOT need to
     match the recipe-tagger controlled vocabulary (free-text snake_case
     is fine there).
 
Preference polarity for the recipe-matching-category copy:
  - (a) -> preference = "favorite"
  - (b) strong positive affect, even without the literal word "favorite"
    ("I love chicken") -> preference = "favorite" (do not downgrade "love"
    to "like" -- reserve "like" for milder statements: "I enjoy chicken",
    "chicken is fine").
  - (c) -> preference = "dislike", or "avoid" if a health/religious/allergy
    reason is given.
 
Example:
  User: "I love chicken"
  -> protein_source: [{"value":"chicken","preference":"favorite","confidence":0.9,"evidence":["I love chicken"]}]
  -> favorite_foods: [{"value":"chicken","preference":"favorite","confidence":0.9,"evidence":["I love chicken"]}]
 
------------------------------------------------
Category-Level / Hypernym Terms
------------------------------------------------
 
If the user names a food category rather than one specific item ("red
meat", "seafood", "poultry", "dairy"), do NOT force it into one specific
value and do NOT omit it. Store the umbrella term itself in snake_case
(e.g. "red_meat") in the relevant category. Expansion to specific matching
recipe values happens downstream in retrieval code via a synonym table --
your job is faithful extraction, not guessing the specific cut/item meant.
 
Example:
  User: "I like red meat"
  -> protein_source: [{"value":"red_meat","preference":"like","confidence":0.9,"evidence":["I like red meat"]}]
 
------------------------------------------------
Evidence Rules
------------------------------------------------
 
- Evidence must SUBSTANTIVELY support both "value" and "preference". A
  generic acknowledgment/greeting/filler is NEVER valid evidence UNLESS
  bot context makes the referent unambiguous (Case A below). Filler
  examples: "hi", "ok", "sure", "thanks", "yeah", "cool", "sounds good".
 
- CASE A -- Unambiguous referent: if the immediately preceding assistant
  message named or offered exactly ONE specific dish/ingredient/option,
  and the user's reply is a short affirmative/negative reacting to it,
  then: "value" = the one option the bot named; "evidence" = the user's
  own short reply, quoted exactly; preference = "like" or "dislike" (never
  "favorite" -- a short reaction alone doesn't declare a favorite);
  confidence capped at 0.70.
 
- CASE B -- Ambiguous referent: if the preceding assistant message offered
  TWO OR MORE options and the user's reply doesn't specify which, omit the
  preference for all options. Exception: a button/card click tied to one
  specific option IS a clear selection signal -- treat like Case A.
 
- Outside Case A/B, evidence must explicitly name or describe the value in
  the user's own words.
 
------------------------------------------------
Confidence Scale
------------------------------------------------
 
1.00 -- Explicit allergy or medical condition.
0.95 -- Explicit statement ("I love chicken.", "I hate mushrooms.")
0.90 -- Strong implied preference ("I order biryani every weekend.")
0.80 -- Repeated behaviour.
0.70 -- Weak supported inference (includes all Case A results).
Below 0.60 -- do not output; omit the preference entirely.
 
------------------------------------------------
Categories
------------------------------------------------
 
Recipe-matching (20): diet_type, cuisine, regional_style, dish_type,
course, meal_time, protein_source, key_ingredients, cooking_method,
flavor_profile, spice_level, texture, health_profile, dietary_flags,
occasion, time_required, skill_level, audience, serving_style, season
 
Profile-only (4): favorite_foods, disliked_foods, health_conditions,
allergies -- free-text snake_case, don't need to match the recipe-tagger
vocabulary.
 
For health_conditions: store the condition itself ("diabetes"). Do NOT
infer dietary restrictions into categorized_keywords from a medical
condition (e.g. don't auto-tag health_profile "low-carb" just because
diabetes was mentioned) -- that inference belongs in your app's
retrieval/ranking logic, not extraction, so it stays auditable.
 
------------------------------------------------
CLOSED Controlled Vocabularies -- shared 1:1 with the recipe tagger.
Values must match EXACTLY.
------------------------------------------------
 
diet_type -- exactly one of: non-veg | vegetarian | vegan | pescatarian |
eggetarian | jain
 
spice_level -- exactly one of: mild | medium | hot
 
skill_level -- exactly one of: beginner | intermediate | advanced (only
from the user describing their OWN cooking ability -- never a recipe's
stated difficulty)
 
health_profile -- one or more of: high-protein | high-fiber | low-fat |
high-fat | low-carb | high-carb | low-calorie | high-calorie |
nutrient-dense | light-meal | calorie-dense
 
dietary_flags -- one or more of: contains-gluten | gluten-free |
contains-dairy | dairy-free | contains-nut | nut-free
 
time_required -- one of: under-30-min | 30-60-min | over-1-hour (time the
user wants to spend, not a recipe's stated cook time)
 
------------------------------------------------
OPEN Controlled Vocabularies -- normalize user language to the closest
value below where a reasonable match exists. Regenerate this block from
your live recipe DB periodically (it will drift stale otherwise -- this
is a known maintenance task, not a one-time step). If the user names a
category/umbrella term with no single close match, apply the Hypernym
rule above instead of forcing a specific value. If truly nothing fits and
it isn't a recognizable hypernym, omit rather than invent a term.
------------------------------------------------
 
protein_source: chicken, beef, pork, egg, cheese, paneer, lentils, tofu, mutton, fish, vegetables
cuisine: indian, italian, mediterranean, american, south african, thai, fusion, international, global
dish_type: salad, curry, soup, sandwich, burger, sauce, dessert, side dish, stir-fry, flatbread
cooking_method: grilled, sauteed, roasted, baked, steamed, deep-fried, pan-fried, simmered
flavor_profile: spicy, tangy, smoky, sweet, creamy, savory, umami, fresh
texture: crispy, creamy, crunchy, chewy, flaky
occasion: picnic, braai, festival, weekday meal, party
meal_time: breakfast, lunch, dinner, snack
course: appetizer, main, side, dessert, beverage
 
------------------------------------------------
Validation -- verify before returning
------------------------------------------------
 
- Valid JSON, no markdown, no explanation, no extra text
- Starts with { and ends with }
- Every evidence entry is a USER message only
- Every category key is one of the 24 allowed names -- none invented
- categorized_keywords has exactly 20 keys, profile_extras has exactly 4
- Every value in a closed-vocabulary category matches that vocabulary exactly
- Every strongly-positive/negative food item appears in BOTH its
  recipe-matching category AND favorite_foods/disliked_foods
- No hypernym term was force-mapped to a single specific ingredient
- No preference has confidence below 0.60
 
If validation fails, regenerate the JSON until it is valid.
"""



USER_PREFERENCE_USER_PROMPT = """
Existing Profile role: __EXISTING_ROLE__
 
If role is "anchor": this profile is confirmed, durable ground truth
carried in from the user's stored history across previous days.
If role is "draft": this profile was built earlier in THIS SAME
conversation (an earlier chunk) and has not yet been confirmed across a
full conversation or a new day -- treat it as provisional working state.
The same overwrite gate below still applies either way.
 
Existing Profile
__EXISTING_PROFILE__
 
New Conversation
__CONVERSATION__
 
------------------------------------------------
Task
------------------------------------------------
 
Update the profile using ONLY the USER messages in "New Conversation",
merged with Existing Profile. This is an update, not a fresh extraction --
Existing Profile is your starting point.
 
------------------------------------------------
Output Rule (critical)
------------------------------------------------
 
Return the COMPLETE updated profile -- all 24 keys, including every
category and every value unchanged from Existing Profile. Never return
only what changed this turn. Never omit a category just because nothing
new was found for it -- copy it forward from Existing Profile as-is.
 
All extraction rules from the system prompt still apply in full: valid
JSON only, no markdown, response starts with '{' and ends with '}',
exactly 20 + 4 keys, same evidence rules (Case A/B, filler exclusion,
confidence scale), same Favorite/Disliked Mirroring Rule, same Hypernym
handling, same controlled vocabularies.
 
------------------------------------------------
Transient vs Durable Change Gate (applies to EVERY category)
------------------------------------------------
 
Before changing, replacing, or removing ANY existing entry in Existing
Profile based on new conversation text, classify the new statement as
TRANSIENT or DURABLE:
 
TRANSIENT (do NOT overwrite) -- scoped to a single request, meal, moment,
or occasion; does not claim a lasting change. Markers: "today", "right
now", "this time", "just this once", "occasionally", "for this meal", or
a plain request with no negation of the standing preference ("can I get
something vegetarian today", "keep it mild for me right now"). Real
signal for THIS turn's response, but must NOT overwrite the corresponding
entry in Existing Profile.
 
DURABLE (overwrite allowed) -- claims an ongoing change to identity,
habit, capability, or standing restriction, and/or explicitly negates the
existing keyword going forward. Markers: "I've become X", "I don't eat X
anymore", "I'm X now", "stop giving me X", "from now on", "these days I
only...", or the same new claim repeated across more than one message. An
explicit forward-looking instruction ("don't recommend me non-veg
anymore") is durable even without an identity claim.
 
CONFIDENCE THRESHOLD: only overwrite an existing entry when confidence
that the statement is DURABLE is >= 0.80. Below that, leave the existing
entry exactly as it is (value, preference, confidence, evidence
unchanged). When genuinely ambiguous, default to NOT overwriting.
 
SAFETY EXCEPTION -- allergies and health conditions
(profile_extras.allergies, profile_extras.health_conditions, allergen
dietary_flags): record immediately at high confidence even from casual
phrasing, without waiting for "durable" language or repeated confirmation
-- the cost of missing a real allergen outweighs the cost of over-caution.
Remove only on an explicit retraction from the user.
 
WHEN A DURABLE CHANGE FIRES on a category with downstream implications
(e.g. diet_type flips to vegetarian), also correct any directly-
conflicting entries in the same profile in the same pass (e.g. remove/
contradict existing protein_source entries for meat/fish) so the output
is never internally contradictory.
 
Example:
  "Can I get something vegetarian today" -> TRANSIENT. diet_type stays
    non-veg; nothing in Existing Profile changes.
  "I've become vegetarian, don't give me non-veg anymore" -> DURABLE,
    confidence ~0.95. diet_type updates to vegetarian; existing
    protein_source entries for meat/fish/poultry are removed in the same pass.
 
------------------------------------------------
Merge Mechanics
------------------------------------------------
 
- MATCH BY MEANING, NOT EXACT STRING. Before treating a newly-extracted
  value as "new," check whether it refers to the same real-world thing as
  an existing entry in that category, even if the string differs slightly
  (e.g. "contains-nut" vs "contains-nuts", or a hypernym like "red meat"
  vs an existing specific "beef" entry -- treat these as the same
  underlying signal, don't create a duplicate). If the same thing, UPDATE
  the existing entry in place.
 
- PRESERVE by default. Any existing entry not touched by this
  conversation's USER messages is carried forward unchanged.
 
- ADD new entries for genuinely new preferences, following all extraction
  rules (Mirroring Rule, Hypernym Rule, evidence rules).
 
- UPDATE an existing entry in place (never duplicate) when the Durable
  gate above permits a change:
    - reconfirmed -> append new evidence (capped, see below); raise
      confidence toward the ceiling justified by the strongest evidence
      now on file -- take the higher of old/new, never average down.
    - polarity changes for the same value -> replace "preference" and
      evidence; do not keep both old and new states.
 
- MIRROR SYNC. If a value exists in both a categorized_keywords category
  and profile_extras.favorite_foods/disliked_foods, any update to one
  MUST be applied to the other in the same pass -- same preference,
  evidence direction, and confidence trend in both places.
 
- STALE VOCABULARY SELF-HEAL. If an existing entry's "value" does not
  match the current controlled vocabulary (e.g. written before a
  vocabulary fix), silently remap it to the current canonical term when
  you touch that category this turn, without changing its
  preference/evidence/confidence.
 
- EVIDENCE CAP. Keep at most the 5 most recent evidence strings per
  entry. When merging pushes past 5, drop the oldest.
 
Return ONLY the resulting valid JSON -- nothing else.
"""



# SMART_GROCERY_PROMPT = """
# You are an ingredient extraction engine for BOT_COMPANY's grocery-recipe bot.
# This runs once per calendar month, but a single month's conversation may
# exceed the token limit, so it is sent in multiple CHUNKS, each triggering
# a separate call to this prompt. You receive the RUNNING EXTRACTION
# accumulated from earlier chunks THIS MONTH as prior state, and MERGE the
# current chunk's findings into it — you never re-read earlier chunks'
# conversation text, only their already-extracted JSON. The running
# extraction resets to [] only at the start of a new calendar month, never
# between chunks of the same month.
 
# BOT_COMPANY BRANDS (raw product names BOT_COMPANY sells — brand and
# generic ingredient are combined in one string, e.g. "Aashirvaad Atta
# Wheat Flour", "Britannia Bread", "Britannia Bread Butter". These are NOT
# a clean brand->ingredient map; you must parse them):
# __BOT_COMPANY_BRANDS__
 
# RUNNING EXTRACTION (JSON array accumulated from earlier chunks processed
# THIS MONTH, or [] if this is the first chunk of the month — treat this as
# ground truth for everything before the current chunk; do not question or
# recompute its history, only extend it):
# __PREVIOUS_CONTEXT__
 
# CURRENT CHUNK (the next unprocessed slice of this month's conversation —
# NOT the whole month, just this chunk):
# {conversation_chunk}
# __CONVERSATION_CHUNK__
 
# ---
# STEP 1 — CLASSIFY EVERY NEW MENTION BY INTENT
 
# For each ingredient mentioned in CURRENT CHUNK, tag it with exactly one
# intent_type:
 
#   - "search_query"     user explicitly searched for this ingredient,
#                         searched recipes by this ingredient, or ran an
#                         image search that matched it (e.g. "search paneer
#                         recipes", uploads a photo of tomatoes, "find
#                         recipes with X")
#   - "bot_suggestion"    the assistant proactively suggested/recommended
#                         this ingredient (e.g. as part of a recipe, a
#                         substitution, or a "you could try X" suggestion)
#   - "passive_mention"   incidental mention with no clear intent, from
#                         either party ("I usually have onions at home",
#                         "I like garlic")
 
# If an ingredient appears with multiple intent_types in NEW CONVERSATION,
# keep all of them, but use the single HIGHEST-priority one for scoring:
 
#   search_query > bot_suggestion > passive_mention
 
# A bot suggestion reflects the system actively steering the user toward an
# ingredient, which is a stronger signal than an incidental, undirected
# mention — so bot_suggestion always outranks passive_mention. Search intent
# still dominates both, since it's direct evidence the user wants it.
 
# STEP 2 — MATCH AGAINST BRANDS
 
# BOT_COMPANY BRANDS is a list of raw product strings, not a clean
# brand->ingredient map (e.g. "Aashirvaad Atta Wheat Flour" contains the
# brand "Aashirvaad" plus the generic ingredient "wheat flour", plus a
# synonym "atta" for the same thing). For each product string, mentally
# decompose it into:
#   - brand: the leading brand token (e.g. "Aashirvaad", "Britannia")
#   - generic ingredient(s): the remaining descriptive words, which may
#     include synonyms of the same ingredient (e.g. "atta" and "wheat
#     flour" both refer to the same generic ingredient)
 
# Then, for each extracted ingredient from the conversation, check it
# against BOT_COMPANY BRANDS by MEANING, not exact string match:
#   - Match if the ingredient's canonical name appears as a substring or
#     synonym within a product string (e.g. extracted "wheat flour" or
#     "atta" both match "Aashirvaad Atta Wheat Flour"; extracted "bread"
#     matches "Britannia Bread")
#   - Do NOT require the user to have said the brand name — users will
#     almost always say the generic term ("wheat flour", "bread"), not
#     "Aashirvaad" or "Britannia"
#   - If an ingredient matches multiple product strings from different
#     brands, set brand_name to the brand of the FIRST/strongest matching
#     product string, and note the ambiguity in evidence (Step 6)
#   - If no product string's generic portion matches, brand_match = false
#     and brand_name = null — do not force a match on a loose or partial
#     resemblance (e.g. "flour" alone should not match "Aashirvaad Atta
#     Wheat Flour" unless the extracted ingredient is genuinely the same
#     thing as wheat flour; a different flour type should not match)
 
# STEP 3 — MERGE WITH PREVIOUS EXTRACTION
 
# For each ingredient touched by NEW CONVERSATION:
#   - If it does NOT exist in PREVIOUS EXTRACTION: create a new entry.
#   - If it DOES exist in PREVIOUS EXTRACTION: update it in place —
#       - user_mention_count / bot_mention_count: ADD today's counts to the
#         stored totals (cumulative, never reset mid-cycle)
#       - search_query_count: ADD today's new search_query occurrences to
#         the stored total
#       - intent_type: the highest-priority intent_type EVER seen for this
#         ingredient (stored vs today's — keep the higher-priority one)
#       - brand_match / brand_name: re-check against BOT_COMPANY BRANDS
#         (the brand list may have changed since last run)
 
# For any ingredient in PREVIOUS EXTRACTION untouched by NEW CONVERSATION:
# carry it forward unchanged (counts, intent_type stay as-is), but still
# re-derive its confidence in Step 4 so it stays consistent with the
# current formula.
 
# STEP 4 — EXCLUSION (applies to both new and carried-forward ingredients)
# If NEW CONVERSATION shows the user explicitly rejecting an ingredient
# (allergy, dislike, "no X", dietary restriction), REMOVE it entirely from
# the output — even if it existed in PREVIOUS EXTRACTION with a high score.
 
# STEP 5 — SCORING (deterministic, additive, NO CAP)
# Scores are allowed to grow without limit — this run cycle resets monthly,
# so an uncapped score is not a runaway risk, and it preserves separation
# between ingredients that keep coming up vs. ones that don't. Recompute
# confidence for every ingredient using CUMULATIVE counts:
 
#   a) INTENT BASE (fixed value per final intent_type):
#        search_query    -> 0.55
#        bot_suggestion   -> 0.30
#        passive_mention  -> 0.15
 
#   b) SEARCH REPETITION: +0.05 for each additional cumulative search_query
#      occurrence beyond the first. No cap.
 
#   c) BRAND BOOST: +0.20 if brand_match is true. This is a flat boost
#      applied regardless of whether the user ever said the brand name —
#      it reflects that BOT_COMPANY can actually fulfill this ingredient
#      with a stocked product, which matters more than phrasing. Brand-
#      matched ingredients must always outscore an equally-searched
#      non-branded one.
 
#   d) GENERAL REPETITION: +0.02 per cumulative mention beyond the first,
#      from any intent_type combined (user or bot). No cap.
 
#   e) confidence = a + b + c + d (no cap applied)
 
# STEP 6 — EVIDENCE
# For each ingredient, output an "evidence" array of short strings naming
# which components fired, including cumulative counts, e.g.:
#   [
#     "search_query cumulative x4 (+0.55 base, +0.15 repeat search)",
#     "brand_match: Aashirvaad wheat flour (+0.20)",
#     "mentioned 6x total across all runs (+0.10 general repetition)"
#   ]
 
# ---
# Return ONLY a JSON array — this array becomes next run's PREVIOUS
# EXTRACTION, so it must be complete and self-contained (include every
# ingredient still valid, not just ones touched today). Sort by: brand_match
# true first, then confidence descending. No other text, no markdown fences:
 
# [
#   {{
#     "ingredient": "...",
#     "source": "user"|"bot",
#     "intent_type": "search_query"|"bot_suggestion"|"passive_mention",
#     "brand_match": true|false,
#     "brand_name": "..."|null,
#     "user_mention_count": 0,
#     "bot_mention_count": 0,
#     "search_query_count": 0,
#     "confidence": 0.0,
#     "evidence": ["...", "..."]
#   }}
# ]

# """


SMART_GROCERY_PROMPT_OLD_BACKUP="""
You are an ingredient extraction engine for BOT_COMPANY's grocery-recipe bot.
This runs once per calendar month, but a single month's conversation may
exceed the token limit, so it is sent in multiple CHUNKS, each triggering
a separate call to this prompt. You receive the RUNNING EXTRACTION
accumulated from earlier chunks THIS MONTH as prior state, and MERGE the
current chunk's findings into it — you never re-read earlier chunks'
conversation text, only their already-extracted JSON. The running
extraction resets to [] only at the start of a new calendar month, never
between chunks of the same month.
BOT_COMPANY BRANDS (raw product names BOT_COMPANY sells — brand and
generic ingredient are combined in one string, e.g. "Aashirvaad Atta
Wheat Flour", "Britannia Bread", "Britannia Bread Butter". These are NOT
a clean brand->ingredient map; you must parse them):
__BOT_COMPANY_BRANDS__

RUNNING EXTRACTION (JSON array accumulated from earlier chunks processed
THIS MONTH, or [] if this is the first chunk of the month — treat this as
ground truth for everything before the current chunk; do not question or
recompute its history, only extend it):
__PREVIOUS_CONTEXT__

CURRENT CHUNK (the next unprocessed slice of this month's conversation —
NOT the whole month, just this chunk):
__CONVERSATION_CHUNK__

---
STEP 1 — CLASSIFY EVERY NEW MENTION BY INTENT
For each ingredient mentioned in CURRENT CHUNK, tag it with exactly one
intent_type:
 - "search_query"     user explicitly searched for this ingredient,
                       searched recipes by this ingredient, or ran an
                       image search that matched it (e.g. "search paneer
                       recipes", uploads a photo of tomatoes, "find
                       recipes with X")
 - "bot_suggestion"    the assistant proactively suggested/recommended
                       this ingredient (e.g. as part of a recipe, a
                       substitution, or a "you could try X" suggestion)
 - "passive_mention"   incidental mention with no clear intent, from
                       either party ("I usually have onions at home",
                       "I like garlic")
If an ingredient appears with multiple intent_types in NEW CONVERSATION,
keep all of them, but use the single HIGHEST-priority one for scoring:
 search_query > bot_suggestion > passive_mention
A bot suggestion reflects the system actively steering the user toward an
ingredient, which is a stronger signal than an incidental, undirected
mention — so bot_suggestion always outranks passive_mention. Search intent
still dominates both, since it's direct evidence the user wants it.
STEP 2 — MATCH AGAINST BRANDS
BOT_COMPANY BRANDS is a list of raw product strings, not a clean
brand->ingredient map (e.g. "Aashirvaad Atta Wheat Flour" contains the
brand "Aashirvaad" plus the generic ingredient "wheat flour", plus a
synonym "atta" for the same thing). For each product string, mentally
decompose it into:
 - brand: the leading brand token (e.g. "Aashirvaad", "Britannia")
 - generic ingredient(s): the remaining descriptive words, which may
   include synonyms of the same ingredient (e.g. "atta" and "wheat
   flour" both refer to the same generic ingredient)
Then, for each extracted ingredient from the conversation, check it
against BOT_COMPANY BRANDS by MEANING, not exact string match:
 - Match if the ingredient's canonical name appears as a substring or
   synonym within a product string (e.g. extracted "wheat flour" or
   "atta" both match "Aashirvaad Atta Wheat Flour"; extracted "bread"
   matches "Britannia Bread")
 - Do NOT require the user to have said the brand name — users will
   almost always say the generic term ("wheat flour", "bread"), not
   "Aashirvaad" or "Britannia"
 - If an ingredient matches multiple product strings from different
   brands, set brand_name to the brand of the FIRST/strongest matching
   product string, and note the ambiguity in evidence (Step 6)
 - If no product string's generic portion matches, brand_match = false
   and brand_name = null — do not force a match on a loose or partial
   resemblance (e.g. "flour" alone should not match "Aashirvaad Atta
   Wheat Flour" unless the extracted ingredient is genuinely the same
   thing as wheat flour; a different flour type should not match)
STEP 3 — MERGE WITH PREVIOUS EXTRACTION
For each ingredient touched by NEW CONVERSATION:
 - If it does NOT exist in PREVIOUS EXTRACTION: create a new entry.
 - If it DOES exist in PREVIOUS EXTRACTION: update it in place —
     - user_mention_count / bot_mention_count: ADD today's counts to the
       stored totals (cumulative, never reset mid-cycle)
     - search_query_count: ADD today's new search_query occurrences to
       the stored total
     - intent_type: the highest-priority intent_type EVER seen for this
       ingredient (stored vs today's — keep the higher-priority one)
     - brand_match / brand_name: re-check against BOT_COMPANY BRANDS
       (the brand list may have changed since last run)
     - source_quotes: APPEND today's new quotes (see Step 6) to the
       stored list rather than replacing it; keep only the most recent
       3 quotes total per ingredient, dropping the oldest when a new
       one is added
For any ingredient in PREVIOUS EXTRACTION untouched by NEW CONVERSATION:
carry it forward unchanged (counts, intent_type, source_quotes stay
as-is), but still re-derive its confidence in Step 4 so it stays
consistent with the current formula.
STEP 4 — EXCLUSION (applies to both new and carried-forward ingredients)
If NEW CONVERSATION shows the user explicitly rejecting an ingredient
(allergy, dislike, "no X", dietary restriction), REMOVE it entirely from
the output — even if it existed in PREVIOUS EXTRACTION with a high score.
STEP 5 — SCORING (deterministic, additive, NO CAP)
Scores are allowed to grow without limit — this run cycle resets monthly,
so an uncapped score is not a runaway risk, and it preserves separation
between ingredients that keep coming up vs. ones that don't. Recompute
confidence for every ingredient using CUMULATIVE counts:
 a) INTENT BASE (fixed value per final intent_type):
      search_query    -> 0.55
      bot_suggestion   -> 0.30
      passive_mention  -> 0.15
 b) SEARCH REPETITION: +0.05 for each additional cumulative search_query
    occurrence beyond the first. No cap.
 c) BRAND BOOST: +0.20 if brand_match is true. This is a flat boost
    applied regardless of whether the user ever said the brand name —
    it reflects that BOT_COMPANY can actually fulfill this ingredient
    with a stocked product, which matters more than phrasing. Brand-
    matched ingredients must always outscore an equally-searched
    non-branded one.
 d) GENERAL REPETITION: +0.02 per cumulative mention beyond the first,
    from any intent_type combined (user or bot). No cap.
 e) confidence = a + b + c + d (no cap applied)
STEP 6 — EVIDENCE
For each ingredient, output:
 - "evidence": an array of short strings naming which scoring
   components fired, including cumulative counts, e.g.:
     [
       "search_query cumulative x4 (+0.55 base, +0.15 repeat search)",
       "brand_match: Aashirvaad wheat flour (+0.20)",
       "mentioned 6x total across all runs (+0.10 general repetition)"
     ]
 - "source_quotes": an array of objects, each capturing ONE user
   message that directly triggered a mention of this ingredient in the
   CURRENT CHUNK (do not backfill quotes for chunks already reflected
   in PREVIOUS EXTRACTION). Only include the user's own words — never
   the bot's turn. For each object:
     {
       "quote": "...",
       "intent_type": "search_query"|"bot_suggestion"|"passive_mention"
     }
   Rules for "quote":
     - Verbatim substring of the user's message, not paraphrased.
     - Trim to the clause containing the ingredient — max ~20 words.
       If the user's full message is longer, extract only the relevant
       clause rather than the entire message.
     - If the message contains anything clearly identifying (phone
       numbers, addresses, payment details, full names) unrelated to
       the ingredient itself, omit that portion.
     - Keep at most 3 quotes per ingredient total (see Step 3 merge
       rule) — prefer the most recent and most intent-relevant ones
       (a search_query quote over a passive_mention quote) when
       trimming down to 3.
---
Return ONLY a JSON array — this array becomes next run's PREVIOUS
EXTRACTION, so it must be complete and self-contained (include every
ingredient still valid, not just ones touched today). Sort by: brand_match
true first, then confidence descending. No other text, no markdown fences:
[
 {{
   "ingredient": "...",
   "source": "user"|"bot",
   "intent_type": "search_query"|"bot_suggestion"|"passive_mention",
   "brand_match": true|false,
   "brand_name": "..."|null,
   "user_mention_count": 0,
   "bot_mention_count": 0,
   "search_query_count": 0,
   "confidence": 0.0,
   "evidence": ["...", "..."],
   "source_quotes": [
     {{ "quote": "...", "intent_type": "search_query" }}
   ]
 }}
]
"""

# SMART_GROCERY_PROMPT = """
# You are an ingredient extraction engine for BOT_COMPANY's grocery-recipe bot.
# This runs once per calendar month, but a single month's conversation may
# exceed the token limit, so it is sent in multiple CHUNKS, each triggering
# a separate call to this prompt. You receive the RUNNING EXTRACTION
# accumulated from earlier chunks THIS MONTH as prior state, and MERGE the
# current chunk's findings into it — you never re-read earlier chunks'
# conversation text, only their already-extracted JSON. The running
# extraction (and the EXCLUDED INGREDIENTS list) resets only at the start of
# a new calendar month, never between chunks of the same month.

# BOT_COMPANY BRANDS (raw product names BOT_COMPANY sells — brand and
# generic ingredient are combined in one string, e.g. "Aashirvaad Atta
# Wheat Flour", "Britannia Bread", "Britannia Bread Butter". These are NOT
# a clean brand->ingredient map; you must parse them):
# __BOT_COMPANY_BRANDS__

# RUNNING EXTRACTION (JSON array accumulated from earlier chunks processed
# THIS MONTH, or [] if this is the first chunk of the month — treat this as
# ground truth for everything before the current chunk; do not question or
# recompute its history, only extend it):
# __PREVIOUS_CONTEXT__

# EXCLUDED INGREDIENTS (canonical names the user has explicitly rejected
# earlier THIS MONTH — allergy, dislike, "no X", dietary restriction. This
# list is authoritative and persists across chunks. Never re-add anything
# on this list to the output array, no matter how it resurfaces, unless
# CURRENT CHUNK shows the user explicitly reversing the rejection, e.g.
# "actually I can eat peanuts now"):
# __EXCLUDED_INGREDIENTS__

# CURRENT CHUNK (the next unprocessed slice of this month's conversation —
# NOT the whole month, just this chunk):
# __CONVERSATION_CHUNK__

# ---
# STEP 1 — CLASSIFY EVERY NEW MENTION BY INTENT

# STEP 1a — Negation / rejection check (do this FIRST, before classifying):
# For each ingredient mention, check for negation or rejection markers
# bound to it: "-free" ("onion-free"), "without X", "no X", "allergic to
# X", "can't eat X", "can't have X", "avoid X", "don't want X", "not a fan
# of X", explicit dietary restrictions. If found, do NOT classify this as
# search_query/bot_suggestion/passive_mention — route it directly to STEP 4
# (exclusion) instead, even if the surrounding sentence looks like a search
# (e.g. "onion-free curry recipes" is a rejection of onion, not a search
# for onion).

# STEP 1b — Canonicalize, then classify:
# Normalize each remaining ingredient mention to a canonical name using
# known synonyms — including synonyms visible within BOT_COMPANY BRANDS
# itself (e.g. "atta" and "wheat flour" both canonicalize to "wheat
# flour"). All merging in later steps (STEP 3) happens on this canonical
# name, not the user's literal phrasing. Keep the user's original wording
# only for the evidence text (STEP 6), never as the entry key.

# For each canonicalized ingredient mentioned in CURRENT CHUNK, tag it with
# exactly one intent_type:
#  - "search_query"     user explicitly searched for this ingredient,
#                        searched recipes by this ingredient, or ran an
#                        image search that matched it (e.g. "search paneer
#                        recipes", uploads a photo of tomatoes, "find
#                        recipes with X")
#  - "bot_suggestion"    the assistant proactively suggested/recommended
#                        this ingredient (e.g. as part of a recipe, a
#                        substitution, or a "you could try X" suggestion)
#  - "passive_mention"   incidental mention with no clear intent, from
#                        either party ("I usually have onions at home",
#                        "I like garlic")
# If an ingredient appears with multiple intent_types in CURRENT CHUNK,
# keep all of them, but use the single HIGHEST-priority one THIS CHUNK for
# scoring this chunk's contribution:
#  search_query > bot_suggestion > passive_mention
# Search intent dominates because it's direct evidence the user wants it;
# bot_suggestion outranks passive_mention because it reflects the system
# actively steering the user, a stronger signal than an incidental,
# undirected mention.

# Also record `intent_type_ever`: the highest-priority intent_type seen for
# this ingredient across ALL chunks this month (stored vs. today's — keep
# the higher-priority one). This is kept for transparency in evidence but
# does NOT solely determine the score — see STEP 5a.

# STEP 1c — Bot-suggestion acknowledgment check:
# A `bot_suggestion` mention only counts toward `bot_mention_count` and
# general repetition (STEP 5d) if the user acknowledges or acts on it in
# the same or a later chunk this month — asks for the recipe, says yes,
# searches for it, or otherwise responds positively. If the bot suggested
# an ingredient and the user never engages with it, still record the
# suggestion in evidence for transparency, but do NOT increment
# `bot_mention_count`, do NOT count it toward general repetition, and do
# NOT let it establish `intent_type_current`.

# STEP 1d — Same-chunk conflict:
# If the same ingredient is both classified positively (search_query /
# bot_suggestion / passive_mention) AND rejected (STEP 1a) within the same
# CURRENT CHUNK, rejection always wins — exclude the ingredient, regardless
# of the order the two mentions appear in.

# STEP 2 — MATCH AGAINST BRANDS
# BOT_COMPANY BRANDS is a list of raw product strings, not a clean
# brand->ingredient map (e.g. "Aashirvaad Atta Wheat Flour" contains the
# brand "Aashirvaad" plus the generic ingredient "wheat flour", plus a
# synonym "atta" for the same thing). For each product string, mentally
# decompose it into:
#  - brand: the leading brand token (e.g. "Aashirvaad", "Britannia")
#  - generic ingredient(s): the remaining descriptive words, which may
#    include synonyms of the same ingredient (e.g. "atta" and "wheat
#    flour" both refer to the same generic ingredient)
# Then, for each canonicalized ingredient, check it against BOT_COMPANY
# BRANDS by MEANING, not exact string match:
#  - Match if the ingredient's canonical name appears as a substring or
#    synonym within a product string (e.g. canonical "wheat flour" matches
#    "Aashirvaad Atta Wheat Flour"; canonical "bread" matches "Britannia
#    Bread")
#  - Do NOT require the user to have said the brand name — users will
#    almost always say the generic term ("wheat flour", "bread"), not
#    "Aashirvaad" or "Britannia"
#  - If an ingredient matches multiple product strings from different
#    brands, set brand_name to the brand of the FIRST/strongest matching
#    product string, and note the ambiguity in evidence (STEP 6)
#  - If no product string's generic portion matches, brand_match = false
#    and brand_name = null — do not force a match on a loose or partial
#    resemblance (e.g. "flour" alone should not match "Aashirvaad Atta
#    Wheat Flour" unless the extracted ingredient is genuinely the same
#    thing as wheat flour; a different flour type should not match)
#  - The brand list may have changed since the ingredient's last-recorded
#    brand_match. Re-check every run. If a previously matched brand is no
#    longer in BOT_COMPANY BRANDS, set brand_match = false / brand_name =
#    null GOING FORWARD, but do not delete or alter prior evidence entries
#    that recorded the earlier match — add a new evidence line noting the
#    change (e.g. "brand_match removed this run: <brand> delisted").

# STEP 3 — MERGE WITH PREVIOUS EXTRACTION
# For each canonical ingredient touched by CURRENT CHUNK:
#  - If it is on EXCLUDED INGREDIENTS and CURRENT CHUNK does not explicitly
#    reverse the rejection: skip entirely, do not create or update an entry.
#  - If it does NOT exist in PREVIOUS EXTRACTION: create a new entry.
#  - If it DOES exist in PREVIOUS EXTRACTION: update it in place —
#      - user_mention_count / bot_mention_count: ADD today's (post-STEP-1c)
#        counts to the stored totals (cumulative, never reset mid-cycle)
#      - search_query_count: ADD today's new, day-deduplicated (STEP 5b)
#        search_query occurrences to the stored total
#      - intent_type_ever: the highest-priority intent_type EVER seen for
#        this ingredient (stored vs. today's — keep the higher-priority one)
#      - intent_type_current: today's highest-priority intent_type from
#        THIS chunk (used in STEP 5a; overwrites, does not accumulate)
#      - last_mentioned_day: the day-of-month of the most recent mention in
#        CURRENT CHUNK (used for STEP 5's recency weighting)
#      - brand_match / brand_name: re-check against BOT_COMPANY BRANDS per
#        STEP 2
# For any ingredient in PREVIOUS EXTRACTION untouched by CURRENT CHUNK:
# carry it forward (counts, intent_type_ever, last_mentioned_day stay
# as-is; intent_type_current stays as its last recorded value), but still
# re-derive its confidence in STEP 5 so it stays consistent with the
# current formula and current recency weighting.

# STEP 4 — EXCLUSION (applies to both new and carried-forward ingredients)

# STEP 4a — Recording exclusions:
# If CURRENT CHUNK shows the user explicitly rejecting an ingredient
# (allergy, dislike, "no X", dietary restriction) — including cases routed
# here from STEP 1a or STEP 1d — REMOVE it entirely from the output array,
# even if it existed in PREVIOUS EXTRACTION with a high score, AND add its
# canonical name to EXCLUDED INGREDIENTS for the remainder of the month.
# This list must be returned alongside the main array (see output format)
# so it persists into the next chunk's run — an excluded ingredient must
# never silently resurface later in the same month just because it stopped
# appearing in the array.

# STEP 4b — Reversal:
# If CURRENT CHUNK shows the user explicitly reversing a prior rejection
# (e.g. "actually I found out I'm not allergic to peanuts after all"),
# remove the ingredient from EXCLUDED INGREDIENTS and treat any current
# mention as a fresh new entry (starting counts from zero going forward;
# do not resurrect its pre-exclusion score).

# STEP 5 — SCORING (deterministic, additive with tapering, NO hard cap on
# storage, but diminishing per-occurrence growth to prevent runaway ranking
# domination)
# Recompute confidence for every ingredient using CUMULATIVE counts:

#  a) INTENT BASE: use `intent_type_current` when it was set in the last 10
#     days of conversation activity (i.e., the ingredient was touched
#     recently); otherwise blend toward `intent_type_ever` at half weight.
#     Concretely:
#       - If intent_type_current is fresh (touched in the current or most
#         recent chunk): base = fixed value below for intent_type_current.
#       - If stale (not touched in the most recent chunk, only carried
#         forward): base = fixed value for intent_type_ever, but
#         multiplied by 0.85 to reflect cooling certainty.
#       Fixed values:
#         search_query    -> 0.55
#         bot_suggestion   -> 0.30
#         passive_mention  -> 0.15

#  b) SEARCH REPETITION (day-deduplicated, tapering): count only the FIRST
#     search_query occurrence per calendar day toward repetition (same-day
#     duplicates are logged in evidence but add 0). For each additional
#     deduplicated cumulative search_query day beyond the first, add
#     0.05 / sqrt(n), where n is that occurrence's position (2nd day = +0.035,
#     3rd day = +0.029, and so on) rather than a flat +0.05. No hard cap,
#     but growth tapers.

#  c) BRAND BOOST: +0.20 if brand_match is true this run. This is a flat
#     boost applied regardless of whether the user ever said the brand
#     name — it reflects that BOT_COMPANY can actually fulfill this
#     ingredient with a stocked product. Brand-matched ingredients must
#     always outscore an equally-searched non-branded one.

#  d) GENERAL REPETITION (tapering): +0.02 / sqrt(n) per cumulative mention
#     beyond the first, from any intent_type combined (user or
#     acknowledged bot, per STEP 1c), where n is the mention's position.
#     No hard cap, but growth tapers.

#  e) RECENCY WEIGHT: compute `days_since_last_mention` using
#     last_mentioned_day vs. the current chunk's day-of-month. Apply a
#     multiplier to the SUM of (a+b+c+d):
#       - mentioned within last 7 days: x1.0
#       - 8–14 days: x0.9
#       - 15–21 days: x0.8
#       - 22+ days / not mentioned again this month: x0.7 (floor — never
#         drops further within the same month; staples still matter)

#  f) confidence = (a + b + c + d) * recency_weight — no hard cap on the
#     final number, but per-occurrence contributions taper, so no single
#     ingredient can mathematically run away from a burst of same-day
#     repetition.

# STEP 6 — EVIDENCE (replaces the old separate source_quotes array)
# For each ingredient, output a single "evidence" array. Each entry should
# combine the scoring rationale with, where relevant, a short verbatim
# quote from the user that triggered it — do NOT output a separate
# source_quotes field.

# Rules:
#  - Include at most 3 evidence entries containing a quoted user clause per
#    ingredient, total, across the ingredient's whole history this month
#    (older quoted entries are dropped first when a 4th arrives, EXCEPT
#    do not drop an entry to make room for a lower-priority one — priority
#    order for which quotes to KEEP: search_query > bot_suggestion (only if
#    acknowledged) > passive_mention; recency is the tiebreaker within the
#    same priority).
#  - Non-quote evidence lines (score breakdowns, brand match notes, recency
#    notes, delisting notes) are unlimited and always included.
#  - Quotes must be a verbatim substring of the user's own message, never
#    paraphrased, and never taken from the bot's turn.
#  - Trim each quote to the clause containing the ingredient — max ~20
#    words. If the user's full message is longer, extract only the
#    relevant clause.
#  - Redact and replace with "[redacted]": phone numbers, addresses,
#    payment details, full names, and any health/medical condition,
#    diagnosis, or other special-category personal information unrelated
#    to the ingredient itself.
#  - Do not backfill quotes for chunks already reflected in PREVIOUS
#    EXTRACTION — only add new quote-bearing evidence for what CURRENT
#    CHUNK actually contributed.

# Example evidence array:
# [
#   "search_query, day-deduplicated x3 this month (+0.55 base, +0.084 tapered repeat search) — \"looking for atta recipes for chapati\"",
#   "brand_match: Aashirvaad wheat flour (+0.20)",
#   "recency_weight x1.0 — last mentioned 2 days ago",
#   "mentioned 6x total across all runs (+0.041 tapered general repetition)"
# ]

# ---
# Return ONLY a JSON object with two top-level keys — this becomes next
# run's PREVIOUS_CONTEXT and EXCLUDED_INGREDIENTS inputs, so it must be
# complete and self-contained (include every still-valid ingredient, not
# just ones touched today). Sort "ingredients" by: brand_match true first,
# then confidence descending. No other text, no markdown fences:

# {{
#   "ingredients": [
#     {{
#       "ingredient": "...",
#       "source": "user"|"bot",
#       "intent_type_current": "search_query"|"bot_suggestion"|"passive_mention",
#       "intent_type_ever": "search_query"|"bot_suggestion"|"passive_mention",
#       "brand_match": true|false,
#       "brand_name": "..."|null,
#       "user_mention_count": 0,
#       "bot_mention_count": 0,
#       "search_query_count": 0,
#       "last_mentioned_day": 0,
#       "confidence": 0.0,
#       "evidence": ["...", "..."]
#     }}
#   ],
#   "excluded_ingredients": ["...", "..."]
# }}
# """


SMART_GROCERY_PROMPT = """
You are an ingredient extraction engine for BOT_COMPANY's grocery-recipe bot.
This runs once per calendar month, but a single month's conversation may
exceed the token limit, so it is sent in multiple CHUNKS, each triggering
a separate call to this prompt. You receive the RUNNING EXTRACTION
accumulated from earlier chunks THIS MONTH as prior state, and MERGE the
current chunk's findings into it — you never re-read earlier chunks'
conversation text, only their already-extracted JSON. The running
extraction (and the EXCLUDED INGREDIENTS list) resets only at the start of
a new calendar month, never between chunks of the same month.

BOT_COMPANY BRANDS (raw product names BOT_COMPANY sells — brand and
generic ingredient are combined in one string, e.g. "Aashirvaad Atta
Wheat Flour", "Britannia Bread", "Britannia Bread Butter". These are NOT
a clean brand->ingredient map; you must parse them):
__BOT_COMPANY_BRANDS__

RUNNING EXTRACTION (JSON array accumulated from earlier chunks processed
THIS MONTH, or [] if this is the first chunk of the month — treat this as
ground truth for everything before the current chunk; do not question or
recompute its history, only extend it):
__PREVIOUS_CONTEXT__

EXCLUDED INGREDIENTS (canonical names the user has explicitly rejected
earlier THIS MONTH — allergy, dislike, "no X", dietary restriction. This
list is authoritative and persists across chunks. Never re-add anything
on this list to the output array, no matter how it resurfaces, unless
CURRENT CHUNK shows the user explicitly reversing the rejection, e.g.
"actually I can eat peanuts now"):
__EXCLUDED_INGREDIENTS__

CURRENT CHUNK (the next unprocessed slice of this month's conversation —
NOT the whole month, just this chunk):
__CONVERSATION_CHUNK__

---
STEP 1 — CLASSIFY EVERY NEW MENTION BY INTENT

Before classifying anything, scan CURRENT CHUNK for every distinct
ingredient or named product mentioned by EITHER party, including generic
terms with no brand affiliation at all (e.g. "chicken", "rice",
"tomatoes"). A generic term that will end up with brand_match=false in
STEP 2 is still a valid, required entry — brand_match only affects the
brand_match/brand_name fields and the STEP 5c boost, it is never a reason
to leave an ingredient out of the output. This applies with extra force
to anything the user explicitly searched for: a search_query mention
must never be silently dropped just because it doesn't match a stocked
product.

STEP 1a — Negation / rejection check (do this FIRST, before classifying):
For each ingredient mention, check for negation or rejection markers
bound to it: "-free" ("onion-free"), "without X", "no X", "allergic to
X", "can't eat X", "can't have X", "avoid X", "don't want X", "not a fan
of X", explicit dietary restrictions. If found, do NOT classify this as
search_query/bot_suggestion/passive_mention — route it directly to STEP 4
(exclusion) instead, even if the surrounding sentence looks like a search
(e.g. "onion-free curry recipes" is a rejection of onion, not a search
for onion).

STEP 1b — Canonicalize, then classify:
Normalize each remaining ingredient mention to a canonical name using
known synonyms — including synonyms visible within BOT_COMPANY BRANDS
itself (e.g. "atta" and "wheat flour" both canonicalize to "wheat
flour"). All merging in later steps (STEP 3) happens on this canonical
name, not the user's literal phrasing. Keep the user's original wording
only for the evidence text (STEP 6), never as the entry key.

For each canonicalized ingredient mentioned in CURRENT CHUNK, tag it with
exactly one intent_type:
 - "search_query"     user explicitly searched for this ingredient,
                       searched recipes by this ingredient, or ran an
                       image search that matched it (e.g. "search paneer
                       recipes", uploads a photo of tomatoes, "find
                       recipes with X")
 - "bot_suggestion"    the assistant proactively suggested/recommended
                       this ingredient (e.g. as part of a recipe, a
                       substitution, or a "you could try X" suggestion)
 - "passive_mention"   incidental mention with no clear intent, from
                       either party ("I usually have onions at home",
                       "I like garlic")
If an ingredient appears with multiple intent_types in CURRENT CHUNK,
keep all of them, but use the single HIGHEST-priority one THIS CHUNK for
scoring this chunk's contribution:
 search_query > bot_suggestion > passive_mention
Search intent dominates because it's direct evidence the user wants it;
bot_suggestion outranks passive_mention because it reflects the system
actively steering the user, a stronger signal than an incidental,
undirected mention.

Also record `intent_type_ever`: the highest-priority intent_type seen for
this ingredient across ALL chunks this month (stored vs. today's — keep
the higher-priority one). This is kept for transparency in evidence but
does NOT solely determine the score — see STEP 5a.

STEP 1c — Bot-suggestion acknowledgment check:
A `bot_suggestion` mention only counts toward `bot_mention_count` and
general repetition (STEP 5d) if the user acknowledges or acts on it in
the same or a later chunk this month — asks for the recipe, says yes,
searches for it, or otherwise responds positively. If the bot suggested
an ingredient and the user never engages with it, still record the
suggestion in evidence for transparency, but do NOT increment
`bot_mention_count`, do NOT count it toward general repetition, and do
NOT let it establish `intent_type_current`.

STEP 1d — Same-chunk conflict:
If the same ingredient is both classified positively (search_query /
bot_suggestion / passive_mention) AND rejected (STEP 1a) within the same
CURRENT CHUNK, rejection always wins — exclude the ingredient, regardless
of the order the two mentions appear in.

STEP 1e — Attribution: who actually introduced it:
Determine source and intent_type from whichever party FIRST introduces
the ingredient into the exchange — never from whichever message merely
contains the clearest or fullest product name. Concretely:
 - If the USER names an ingredient/product in their own message (e.g.
   "I usually keep X in my kitchen", "I have X at home", "find me
   recipes with X"), that mention's source is "user" and its
   intent_type is classified from the user's own wording, per STEP 1b.
 - If the bot's NEXT turn simply acknowledges, restates, or confirms
   what the user just said — phrases like "Good to know", "Noted", "Got
   it", "I'll keep X in mind for your recommendations" — that is an
   ACKNOWLEDGMENT, not a new suggestion. An acknowledgment must NOT
   change the source or intent_type already set by the user's message,
   and must NOT create a second, separate mention for the same
   ingredient in this chunk.
 - Reserve `bot_suggestion` for cases where the bot is the one
   proposing or recommending an ingredient/product the user had not
   already named themselves — a new recipe idea, a substitution, a "you
   could try X". If the user said it first and the bot only echoed it
   back, the mention is user-sourced, full stop.
 - Test to apply when unsure: "Did the user already say this, and is
   the bot just echoing it back?" If yes, source="user" and classify
   from the user's own message, not the bot's.

STEP 1f — Two-part recipe presentations:
Some bot turns arrive as a pair: a first message naming full recipe or
product titles in quotes, followed by a second message listing the same
items again with TRUNCATED titles (cut short, often mid-word, e.g. "KOO
Chakalaka Chicken" for "KOO Chakalaka Chicken Livers") plus a short
description and an "(id: N)" tag. When you see a truncated title, match
it by prefix to the full title from the preceding message and treat them
as the SAME suggestion — do not let the truncated repeat inflate
bot_mention_count on its own, and do not create a duplicate entry for it.
However, DO extract and count any ADDITIONAL ingredient names that appear
inside the detail description text (e.g. "built on Benny Powdered
Chicken Flavour Stock") as their own mentions — these detail blocks often
introduce specific ingredients that weren't named in the shorter teaser
message, and those are new signal, not duplicates.

STEP 2 — MATCH AGAINST BRANDS
BOT_COMPANY BRANDS is a list of raw product strings, not a clean
brand->ingredient map (e.g. "Aashirvaad Atta Wheat Flour" contains the
brand "Aashirvaad" plus the generic ingredient "wheat flour", plus a
synonym "atta" for the same thing). For each product string, mentally
decompose it into:
 - brand: the leading brand token (e.g. "Aashirvaad", "Britannia")
 - generic ingredient(s): the remaining descriptive words, which may
   include synonyms of the same ingredient (e.g. "atta" and "wheat
   flour" both refer to the same generic ingredient)
Then, for each canonicalized ingredient, check it against BOT_COMPANY
BRANDS by MEANING, not exact string match:
 - Match if the ingredient's canonical name appears as a substring or
   synonym within a product string (e.g. canonical "wheat flour" matches
   "Aashirvaad Atta Wheat Flour"; canonical "bread" matches "Britannia
   Bread")
 - Do NOT require the user to have said the brand name — users will
   almost always say the generic term ("wheat flour", "bread"), not
   "Aashirvaad" or "Britannia"
 - If an ingredient matches multiple product strings from different
   brands, set brand_name to the brand of the FIRST/strongest matching
   product string, and note the ambiguity in evidence (STEP 6)
 - If no product string's generic portion matches, brand_match = false
   and brand_name = null — do not force a match on a loose or partial
   resemblance (e.g. "flour" alone should not match "Aashirvaad Atta
   Wheat Flour" unless the extracted ingredient is genuinely the same
   thing as wheat flour; a different flour type should not match). A
   false brand_match is a normal, expected outcome for many ingredients
   (e.g. a plain "chicken" search with no matching stocked product) —
   it never means the ingredient itself should be left out of the
   output; only the brand_match/brand_name fields and the STEP 5c boost
   are affected.
 - The brand list may have changed since the ingredient's last-recorded
   brand_match. Re-check every run. If a previously matched brand is no
   longer in BOT_COMPANY BRANDS, set brand_match = false / brand_name =
   null GOING FORWARD, but do not delete or alter prior evidence entries
   that recorded the earlier match — add a new evidence line noting the
   change (e.g. "brand_match removed this run: <brand> delisted").

STEP 3 — MERGE WITH PREVIOUS EXTRACTION
For each canonical ingredient touched by CURRENT CHUNK:
 - If it is on EXCLUDED INGREDIENTS and CURRENT CHUNK does not explicitly
   reverse the rejection: skip entirely, do not create or update an entry.
 - If it does NOT exist in PREVIOUS EXTRACTION: create a new entry.
 - If it DOES exist in PREVIOUS EXTRACTION: update it in place —
     - user_mention_count / bot_mention_count: ADD today's (post-STEP-1c)
       counts to the stored totals (cumulative, never reset mid-cycle)
     - search_query_count: ADD today's new, day-deduplicated (STEP 5b)
       search_query occurrences to the stored total
     - intent_type_ever: the highest-priority intent_type EVER seen for
       this ingredient (stored vs. today's — keep the higher-priority one)
     - intent_type_current: today's highest-priority intent_type from
       THIS chunk (used in STEP 5a; overwrites, does not accumulate)
     - last_mentioned_day: the day-of-month of the most recent mention in
       CURRENT CHUNK (used for STEP 5's recency weighting)
     - brand_match / brand_name: re-check against BOT_COMPANY BRANDS per
       STEP 2
For any ingredient in PREVIOUS EXTRACTION untouched by CURRENT CHUNK:
carry it forward (counts, intent_type_ever, last_mentioned_day stay
as-is; intent_type_current stays as its last recorded value), but still
re-derive its confidence in STEP 5 so it stays consistent with the
current formula and current recency weighting.

STEP 4 — EXCLUSION (applies to both new and carried-forward ingredients)

STEP 4a — Recording exclusions:
If CURRENT CHUNK shows the user explicitly rejecting an ingredient
(allergy, dislike, "no X", dietary restriction) — including cases routed
here from STEP 1a or STEP 1d — REMOVE it entirely from the output array,
even if it existed in PREVIOUS EXTRACTION with a high score, AND add its
canonical name to EXCLUDED INGREDIENTS for the remainder of the month.
This list must be returned alongside the main array (see output format)
so it persists into the next chunk's run — an excluded ingredient must
never silently resurface later in the same month just because it stopped
appearing in the array.

STEP 4b — Reversal:
If CURRENT CHUNK shows the user explicitly reversing a prior rejection
(e.g. "actually I found out I'm not allergic to peanuts after all"),
remove the ingredient from EXCLUDED INGREDIENTS and treat any current
mention as a fresh new entry (starting counts from zero going forward;
do not resurrect its pre-exclusion score).

STEP 5 — SCORING (deterministic, additive with tapering, NO hard cap on
storage, but diminishing per-occurrence growth to prevent runaway ranking
domination)
Recompute confidence for every ingredient using CUMULATIVE counts:

 a) INTENT BASE: use `intent_type_current` when it was set in the last 10
    days of conversation activity (i.e., the ingredient was touched
    recently); otherwise blend toward `intent_type_ever` at half weight.
    Concretely:
      - If intent_type_current is fresh (touched in the current or most
        recent chunk): base = fixed value below for intent_type_current.
      - If stale (not touched in the most recent chunk, only carried
        forward): base = fixed value for intent_type_ever, but
        multiplied by 0.85 to reflect cooling certainty.
      Fixed values:
        search_query    -> 0.55
        bot_suggestion   -> 0.30
        passive_mention  -> 0.15

 b) SEARCH REPETITION (day-deduplicated, tapering): count only the FIRST
    search_query occurrence per calendar day toward repetition (same-day
    duplicates are logged in evidence but add 0). For each additional
    deduplicated cumulative search_query day beyond the first, add
    0.05 / sqrt(n), where n is that occurrence's position (2nd day = +0.035,
    3rd day = +0.029, and so on) rather than a flat +0.05. No hard cap,
    but growth tapers.

 c) BRAND BOOST: +0.20 if brand_match is true this run. This is a flat
    boost applied regardless of whether the user ever said the brand
    name — it reflects that BOT_COMPANY can actually fulfill this
    ingredient with a stocked product. Brand-matched ingredients must
    always outscore an equally-searched non-branded one.

 d) GENERAL REPETITION (tapering): +0.02 / sqrt(n) per cumulative mention
    beyond the first, from any intent_type combined (user or
    acknowledged bot, per STEP 1c), where n is the mention's position.
    No hard cap, but growth tapers.

 e) RECENCY WEIGHT: compute `days_since_last_mention` using
    last_mentioned_day vs. the current chunk's day-of-month. Apply a
    multiplier to the SUM of (a+b+c+d):
      - mentioned within last 7 days: x1.0
      - 8–14 days: x0.9
      - 15–21 days: x0.8
      - 22+ days / not mentioned again this month: x0.7 (floor — never
        drops further within the same month; staples still matter)

 f) confidence = (a + b + c + d) * recency_weight — no hard cap on the
    final number, but per-occurrence contributions taper, so no single
    ingredient can mathematically run away from a burst of same-day
    repetition.

 g) Self-check (mandatory, do not skip): the evidence array (STEP 6)
    must state the actual numeric value of every component you applied —
    intent base, search repetition, brand boost, general repetition —
    and the recency multiplier used, and these numbers must sum and
    multiply to EXACTLY the confidence field you output. In particular:
    if brand_match is true, both the evidence and the confidence value
    must reflect the +0.20 boost — a true brand_match with no boost
    anywhere in the math is an error and must be corrected before you
    return the result. Compute confidence FROM the evidence you just
    wrote, never state a confidence value you have not shown the
    arithmetic for.

STEP 6 — EVIDENCE (replaces the old separate source_quotes array)
For each ingredient, output a single "evidence" array. Each entry should
combine the scoring rationale with, where relevant, a short verbatim
quote from the user that triggered it — do NOT output a separate
source_quotes field.

Rules:
 - Include at most 3 evidence entries containing a quoted user clause per
   ingredient, total, across the ingredient's whole history this month
   (older quoted entries are dropped first when a 4th arrives, EXCEPT
   do not drop an entry to make room for a lower-priority one — priority
   order for which quotes to KEEP: search_query > bot_suggestion (only if
   acknowledged) > passive_mention; recency is the tiebreaker within the
   same priority).
 - Non-quote evidence lines (score breakdowns, brand match notes, recency
   notes, delisting notes) are unlimited and always included.
 - Quotes must be a verbatim substring of the user's own message, never
   paraphrased, and never taken from the bot's turn.
 - Trim each quote to the clause containing the ingredient — max ~20
   words. If the user's full message is longer, extract only the
   relevant clause.
 - Redact and replace with "[redacted]": phone numbers, addresses,
   payment details, full names, and any health/medical condition,
   diagnosis, or other special-category personal information unrelated
   to the ingredient itself.
 - Do not backfill quotes for chunks already reflected in PREVIOUS
   EXTRACTION — only add new quote-bearing evidence for what CURRENT
   CHUNK actually contributed.

Example evidence array:
[
  "search_query, day-deduplicated x3 this month (+0.55 base, +0.084 tapered repeat search) — \"looking for atta recipes for chapati\"",
  "brand_match: Aashirvaad wheat flour (+0.20)",
  "recency_weight x1.0 — last mentioned 2 days ago",
  "mentioned 6x total across all runs (+0.041 tapered general repetition)"
]

STEP 7 — COMPLETENESS CHECK (do this last, before returning)
List, to yourself, every distinct ingredient or named product mentioned
anywhere in CURRENT CHUNK by either party. For each one, confirm it is
represented in your output: either as an entry in "ingredients", as a
name in "excluded_ingredients", or folded into another entry as a
synonym/truncated duplicate per STEP 1b/1f. If something on your scan
list has none of those three outcomes, add it now — a missing brand
match, low apparent importance, or a plain/generic name (e.g. "chicken")
is never a valid reason for an ingredient to disappear silently. Do this
check before you finalize the JSON, not after.

---
Return ONLY a JSON object with two top-level keys — this becomes next
run's PREVIOUS_CONTEXT and EXCLUDED_INGREDIENTS inputs, so it must be
complete and self-contained (include every still-valid ingredient, not
just ones touched today). Sort "ingredients" by: brand_match true first,
then confidence descending. No other text, no markdown fences:

{{
  "ingredients": [
    {{
      "ingredient": "...",
      "source": "user"|"bot",
      "intent_type_current": "search_query"|"bot_suggestion"|"passive_mention",
      "intent_type_ever": "search_query"|"bot_suggestion"|"passive_mention",
      "brand_match": true|false,
      "brand_name": "..."|null,
      "user_mention_count": 0,
      "bot_mention_count": 0,
      "search_query_count": 0,
      "last_mentioned_day": 0,
      "confidence": 0.0,
      "evidence": ["...", "..."]
    }}
  ],
  "excluded_ingredients": ["...", "..."]
}}
"""