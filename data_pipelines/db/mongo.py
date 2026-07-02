from datetime import datetime, timezone

from pymongo import MongoClient, UpdateOne

from data_pipelines.core.config import (
    MONGO_DB,
    MONGO_URL,
    RECIPES_COLLECTION,
    SOURCE_ID_FIELD,
)

_client = MongoClient(MONGO_URL,  uuidRepresentation="standard")
_db = _client[MONGO_DB]
_indexes_ensured = False


def get_collection(colection):
    return _db[colection]

def get_recipes_collection():
    return _db[RECIPES_COLLECTION]


def ensure_indexes():
    global _indexes_ensured
    if _indexes_ensured:
        return
    get_recipes_collection().create_index("source_id", unique=True)
    _indexes_ensured = True


def upsert_recipe_batch(records: list[dict], batch_size: int = 1000) -> int:
    ensure_indexes()
    collection = get_recipes_collection()
    now = datetime.now(timezone.utc)
    upserted_count = 0

    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        ops = [
            UpdateOne(
                {"source_id": record[SOURCE_ID_FIELD]},
                {
                    "$set": {"payload": record, "fetched_at": now, "status":"unprocessed"},
                    "$setOnInsert": {"enrichments": {}, "updated_at": now},
                },
                upsert=True,
            )
            for record in batch
        ]
        collection.bulk_write(ops, ordered=False)
        upserted_count += len(batch)

    return upserted_count
