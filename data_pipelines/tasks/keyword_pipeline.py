import asyncio
from datetime import datetime
import uuid

from data_pipelines.core.celery import celery_app
from data_pipelines.core.config import AUDIT_LOGS_COLLECTION
from data_pipelines.db.mongo import get_collection
from data_pipelines.llm.recipe_keyword_pipeline_graph import build_graph

# audit_collection = MONGO_DB["audit_logs"]
audit_collection = get_collection(AUDIT_LOGS_COLLECTION)


async def run_keyword_pipeline():
    # Quick local test: run the graph end-to-end and print final state.
    execution_id = uuid.uuid4()
    state = {
                "execution_id": execution_id,
                "current_chunk":[],
                "total_chunks":0,
                "current_chunk_index":0,
                "current_chunk_tokens":0,
                "processed_data":[]
            }

    try:
        print("Creating Graph========>>>>>")
        graph = build_graph().compile()
        return await graph.ainvoke(state)

    except Exception as e:
        audit_collection.insert_one(
            {
                "execution_id": state["execution_id"],
                "status": "FAILED",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "state": state,
                "created_at": datetime.utcnow(),
            }
        )
        raise


@celery_app.task
def keyword_pipeline():
    asyncio.run(run_keyword_pipeline())
