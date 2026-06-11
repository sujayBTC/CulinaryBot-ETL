from datetime import datetime, timezone

from data_pipelines.recipe_keyword_extraction_pipeline.extractor import extract_keywords
from db.mongo import ensure_indexes, get_recipes_collection
from logger import logger


async def run_recipe_keyword_extraction() -> dict:
    ensure_indexes()
    collection = get_recipes_collection()
    now = datetime.now(timezone.utc)
    updated_count = 0
    skipped_count = 0

    for doc in collection.find({}):
        enrichments = doc.get("enrichments") or {}
        if enrichments.get("keywords"):
            skipped_count += 1
            continue

        keywords = extract_keywords(doc["payload"])
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"enrichments.keywords": keywords, "updated_at": now}},
        )
        updated_count += 1

    logger.info(
        f"Recipe keyword extraction complete "
        f"updated_count={updated_count} skipped_count={skipped_count}"
    )
    return {"updated_count": updated_count, "skipped_count": skipped_count}
