import json
import asyncpg
import asyncio

POSTGRES_URL = "postgresql://user:password@localhost:5432/dbname"

async def import_json():
    with open("data.json", "r") as f:
        data = json.load(f)

    conn = await asyncpg.connect(POSTGRES_URL)

    try:
        await conn.executemany(
            """
            INSERT INTO messages (
                id,
                conversation_id,
                content,
                created_at,
                updated_at
            )
            VALUES ($1, $2, $3::jsonb, $4, $5)
            ON CONFLICT (id) DO NOTHING
            """,
            [
                (
                    item["id"],
                    item["conversation_id"],
                    json.dumps(item["content"]),
                    item["created_at"],
                    item["updated_at"],
                )
                for item in data
            ],
        )
    finally:
        await conn.close()

asyncio.run(import_json())