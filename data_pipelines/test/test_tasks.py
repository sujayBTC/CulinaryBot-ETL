from data_pipelines.tasks.keyword_pipeline import keyword_pipeline
from data_pipelines.tasks.recipe_ingest import recipe_ingest
from data_pipelines.recipe_worker.keyword_worker import keywords_generator
from data_pipelines.db.mongo import get_recipes_collection
# recipe = recipe_ingest.delay()
# print("Triggered recipe Ingest =======================================>")
from data_pipelines.db.mongo import recipe_collection
import datetime
import time
recipes = recipe_collection.find()

batch_start = time.perf_counter()
count = 0
for recipe in recipes:
    print(f"Recipe {recipe['_id']} triggered =======================================>")
    keywords_generator.delay(
        str(recipe["_id"])
    )
    count+=1

queue_time = time.perf_counter() - batch_start
print(
    f"Queued {count} recipes "
    f"in {queue_time:.2f} seconds"
)