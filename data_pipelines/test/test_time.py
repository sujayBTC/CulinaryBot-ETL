from data_pipelines.db.mongo import metadata_collection

first = metadata_collection.find_one(
    {"created_at": {"$exists": True}},
    sort=[("created_at", 1)]
)

last = metadata_collection.find_one(
    {"completed_at": {"$exists": True}},
    sort=[("completed_at", -1)]
)

if first and last:
    total_time = (
        last["completed_at"] -
        first["created_at"]
    ).total_seconds()

    print(
        f"========================>>>>>>>>>>  Total batch time: {total_time:.2f} seconds"
    )