from data_pipelines.tasks.keyword_pipeline import keyword_pipeline
from data_pipelines.tasks.recipe_ingest import recipe_ingest
from data_pipelines.recipe_worker.keyword_worker import keywords_generator
from data_pipelines.db.mongo import get_recipes_collection
from data_pipelines.db.mongo import recipe_collection
import datetime
import time
# recipe = recipe_ingest.delay()
# print("Triggered recipe Ingest =======================================>")


# keyword_pipeline.delay()
# print("Triggered keyword extractor================================")


batch_start = time.perf_counter()
count = 0
for recipe in recipe_collection.find({"metadata_status":"pending"}):
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