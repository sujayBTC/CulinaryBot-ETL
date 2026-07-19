from data_pipelines.tasks.keyword_pipeline import keyword_pipeline
from data_pipelines.tasks.user_preference_task import user_preference_task, today_conversation_ingest_task, send_user_preference_data, all_conersation_ingest_task
from data_pipelines.tasks.recipe_ingest import all_recipe_ingest_task, send_metadata_task, today_recipe_ingest_task, triger_conver_vector_task
from data_pipelines.recipe_worker.keyword_worker import keywords_generator
from data_pipelines.db.mongo import get_recipes_collection
from data_pipelines.db.mongo import recipe_collection
import datetime
import time

from celery import chain, chord
from data_pipelines.core.celery import celery_app

# recipe = all_recipe_ingest_task.delay()
# print("Triggered recipe Ingest =======================================>")


# keyword_pipeline.delay()
# print("Triggered keyword extractor================================")


# today_conversation_ingest_task.delay()
# print("today user conversation ingest task==============================>")

# all_conersation_ingest_task.delay()
# print("all user conversation ingest task==============================>")

# user_preference_task.delay()
# print("User preference keyword extractor================================")


# send_user_preference_data.delay()
# print("triger send send user preference task=================>")


# batch_start = time.perf_counter()
# count = 0
# for recipe in recipe_collection.find({"status": {"$ne": "success"}}):
    
#     print(f"Recipe {recipe['_id']} triggered =======================================>")
#     keywords_generator.delay(
#         str(recipe["_id"])
#     )
#     count+=1

# queue_time = time.perf_counter() - batch_start
# print(
#     f"Queued {count} recipes "
#     f"in {queue_time:.2f} seconds"
#  )


# send_metadata_task.delay()
# print("triger recipe metadata send task=================================>")


triger_conver_vector_task.delay()
print("Triger convert vector task====================>")

@celery_app.task
def run_keyword_pipeline():
    header = [
        keywords_generator.s(str(recipe["_id"]))
        for recipe in recipe_collection.find({"status": {"$ne": "success"}})
    ]
    if not header:
        return
    
    return chord(header)(send_metadata_task.si())


@celery_app.task
def start_keyword_pipeline():
    return chain(
        today_recipe_ingest_task.si(),
        run_keyword_pipeline.si(),
        triger_conver_vector_task.si(),
    ).delay()


@celery_app.task
def run_user_preference_pipeline():
    chain(
        today_conversation_ingest_task.si(),
        user_preference_task.si(),
        send_user_preference_data.si(),
    ).delay()
