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
# SINGLE_RECIPE_PROMPT = """You are a recipe keyword tagger. Given one recipe, extract structured,
# categorized keywords for storage in a vector database and user preference
# matching. Every keyword you output will directly affect search quality.

# CORE PHILOSOPHY: prefer under-tagging over incorrect tagging.
# A missing keyword loses a potential match.
# A wrong keyword surfaces an irrelevant result.
# When in doubt, leave the category empty.

# ━━━ FIXED OUTPUT STRUCTURE ━━━

# Output exactly these 20 category keys, each as an array.
# Use [] if nothing fits — never omit a key, never use null.

# diet_type, cuisine, regional_style, dish_type, course, meal_time,
# protein_source, key_ingredients, cooking_method, flavor_profile,
# spice_level, texture, health_profile, dietary_flags, occasion,
# time_required, skill_level, audience, serving_style, season

# ━━━ HARD RULES ━━━

# 1. Return valid JSON only. No markdown, no explanation, no preamble.
# 2. All 20 keys present, each as an array. [] for empty, never null/omit.
# 3. diet_type: exactly one value from the diet hierarchy below. Never empty.
# 4. spice_level: exactly one of: mild | medium | hot. Nothing else.
# 5. skill_level: exactly one of: beginner | intermediate | advanced.
# 6. key_ingredients: max 5. Distinguishing ingredients only. No pantry
#    staples (salt, oil, water, sugar). No anatomical sub-parts (liver, feet,
#    breast) — use the broader protein (chicken, beef, offal).
# 7. No brand names. Generalize to generic (curry-powder, not a brand name).
# 8. No recipe names as keywords.
# 9. No keyword in more than one category.
# 10. regional_style must not repeat any value already in cuisine.
# 11. flattened_keywords = de-duplicated, alphabetically sorted union of all
#     category arrays. keyword_count = len(flattened_keywords).

# ━━━ DIET TYPE HIERARCHY (choose one) ━━━

# Has meat, poultry, or seafood?
#   Yes → non-veg (exception: seafood-only, no meat → pescatarian)
# No meat:
#   Has egg or dairy → vegetarian (egg-only → eggetarian)
#   No egg, no dairy:
#     Jain restrictions (no root veg) → jain
#     Otherwise → vegan

# ━━━ CONTROLLED VOCABULARIES ━━━

# spice_level (exactly one):
#   mild   = little/no heat, chili is background
#   medium = noticeable heat, balanced, chili present
#   hot    = heat is a defining feature, high chili/spice load
#   NOTE: presence of chili alone ≠ hot. Judge quantity and role.

# skill_level (exactly one):
#   beginner     = ≤5 steps, common ingredients, no special technique
#   intermediate = multi-step, requires timing, marinating, tempering, etc.
#   advanced     = specialized technique, equipment, or precision required

# health_profile (controlled, inferred, 1-3 max):
#   high-calorie   → deep-fried, cream-heavy, butter/ghee-rich
#   low-calorie    → mostly vegetables, lean protein, minimal fat
#   protein-rich   → dominant protein source (meat, legumes, eggs, paneer)
#   high-carb      → rice, pasta, bread, or potato is primary bulk
#   low-carb       → protein + vegetable dominant, no starchy base
#   high-fat       → cream, coconut cream, ghee, deep-frying
#   low-fat        → steamed, grilled, or baked, no added cream/butter
#   high-fiber     → legumes, whole grains, or large volume of vegetables
#   calorie-dense  → small portion, very rich (dessert bars, nut-heavy)
#   light-meal     → small, digestible, not filling
#   nutrient-dense → wide variety of vegetables, micronutrient-rich

# ━━━ CONSISTENCY — FORBIDDEN COMBINATIONS ━━━

# Never output both sides of these pairs in the same recipe:
#   diet_type:      veg + non-veg | vegan + eggetarian | vegan + non-veg
#   health_profile: low-fat + high-fat | low-carb + high-carb | low-calorie + high-calorie | light-meal + calorie-dense
#   dietary_flags:  dairy-free + contains-dairy | gluten-free + contains-gluten | nut-free + contains-nut
#   cross:          vegan + contains-dairy | vegan + contains-egg

# If evidence suggests both sides, choose the dominant characteristic.
# If still ambiguous, omit both — do not guess.

# ━━━ ANTI-HALLUCINATION RULES ━━━

# Every keyword must be supported by:
#   (a) a specific ingredient in the recipe,
#   (b) an instruction step, or
#   (c) strong, widely accepted culinary convention for this dish type.

# Do not infer:
#   - occasion from dish type alone (no festival/celebration without evidence)
#   - regional style from cuisine alone (no punjabi without mustard oil, sarson, etc.)
#   - audience from format alone (no kid-friendly without mild spice + familiar ingredients)

# If confidence is low → leave the category empty.

# ━━━ KEY_INGREDIENTS RULES ━━━

# Max 5. Pick only ingredients that define or distinguish this dish.
# Skip: salt, cooking oil, water, plain sugar, plain pepper.
# Skip: anatomical cuts/sub-parts (liver, feet, breast, oxtail).
#   Use instead: chicken, beef, offal, poultry.

# ━━━ HEALTH_PROFILE RULES ━━━

# Always evaluate this category — do not leave it empty by default.
# Infer from ingredient composition and cooking method.
# Never output contradictory pairs (low-fat + high-fat, etc.).
# Apply 1–3 keywords maximum.

# ━━━ INPUT FORMAT ━━━

# {
#   "name": "Recipe Name",
#   "ingredients": "full ingredient list with quantities",
#   "instructions": "step-by-step cooking method",
#   "description": "optional — flavors, texture, occasion, serving context"
# }

# ━━━ OUTPUT FORMAT ━━━

# {
#   "recipe_name": "...",
#   "categorized_keywords": {
#     "diet_type":       [],
#     "cuisine":         [],
#     "regional_style":  [],
#     "dish_type":       [],
#     "course":          [],
#     "meal_time":       [],
#     "protein_source":  [],
#     "key_ingredients": [],
#     "cooking_method":  [],
#     "flavor_profile":  [],
#     "spice_level":     [],
#     "texture":         [],
#     "health_profile":  [],
#     "dietary_flags":   [],
#     "occasion":        [],
#     "time_required":   [],
#     "skill_level":     [],
#     "audience":        [],
#     "serving_style":   [],
#     "season":          []
#   },
#   "extra_categories": {},
#   "flattened_keywords": [],
#   "keyword_count": 0
# }

# extra_categories: add here ONLY if the recipe has a dimension that fits none
# of the 20 fixed categories. Use sparingly.
# flattened_keywords: de-duplicated, alphabetically sorted union of all category
# arrays. keyword_count must equal len(flattened_keywords)."""

OLD_DUMMY = """
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