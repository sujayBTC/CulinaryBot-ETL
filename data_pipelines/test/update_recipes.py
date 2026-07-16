from data_pipelines.db.mongo import recipe_collection
recipe_collection.update_many({"metadata_status": { "$exists": False }},{"$set": {"metadata_status": "pending"}})
print("==========================>>>>>>>>>>>>>... updated all the recipes with metadata_status")