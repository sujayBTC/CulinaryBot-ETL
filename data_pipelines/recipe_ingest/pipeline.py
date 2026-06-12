import httpx

from config import BACK_END_URL
from db.mongo import upsert_recipe_batch
# from logger import logger


async def run_recipe_ingest() -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(BACK_END_URL)
        response.raise_for_status()

    recipe_data = response.json()
    recipes = recipe_data.get("items", [])

    # logger.info(f"Fetched recipes from backend status={response.status_code}")

    if not recipes:
        # logger.warning("No recipes returned from backend")
        return {"upserted_count": 0}

    upserted_count = upsert_recipe_batch(recipes)
    # logger.info(f"Recipe ingest complete upserted_count={upserted_count}")
    return {"upserted_count": upserted_count}
