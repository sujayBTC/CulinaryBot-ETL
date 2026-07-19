from data_pipelines.langgraph.user_preference_pipeline.user_prefernce_pipeline import user_preference_extraction
from data_pipelines.tasks.conversation_ingest import conersation_ingest, send_keyword, all_conersation_ingest
from data_pipelines.core.celery import celery_app
import asyncio


@celery_app.task
def all_conersation_ingest_task():
    asyncio.run(all_conersation_ingest())

@celery_app.task
def today_conversation_ingest_task():
    asyncio.run(conersation_ingest())

@celery_app.task
def user_preference_task():
    asyncio.run(user_preference_extraction())
    

@celery_app.task
def send_user_preference_data():
    asyncio.run(send_keyword())
