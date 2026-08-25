import json
import tiktoken

from datetime import datetime, timedelta, timezone
from collections import defaultdict
from logger import logger

from langchain_core.messages import HumanMessage, SystemMessage
from data_pipelines.llm.model import llm
from data_pipelines.llm.prompt import SYSTEM_PROMPT, USER_PREFERENCE_PROMPT, USER_PREFERENCE_USER_PROMPT, SMART_GROCERY_PROMPT

from data_pipelines.db.mongo import get_collection

CONVERSATION_COLLECTION = 'conversations'
RECIPE_BRAND_COLLECTION = 'recipe_brand'
SMART_GROCERY_COLLECTION = 'smart_grocery'

MODEL_NAME = "gpt-4o"
MODEL_CONTEXT_WINDOW = 128_000
FIXED_RESERVED_TOKENS = (
    5_000   # system prompt
    + 5_000   # expected response
    + 8_000   # safety buffer
)

try:
    encoder = tiktoken.encoding_for_model(MODEL_NAME)
except KeyError:
    encoder = tiktoken.get_encoding("cl100k_base")


def message_to_text(msg: dict) -> str:
    return f"[{msg['user']}] {msg['content']}"


def count_tokens(text: str) -> int:
    return len(encoder.encode(text))


def remove_duplicates(messages):

    unique = []
    prev_key = None

    for m in messages:
        key = (m["user_id"], m["direction"], m["content"].strip().lower())
        if key != prev_key:
            unique.append(m)
        prev_key = key

    return unique


def group_by_user(messages):
    user_map = defaultdict(list)

    for m in messages:
        user_map[m["user_id"]].append({
            "user": "user" if m["direction"] == "inbound" else "bot",
            "content": m["content"],
        })

    return user_map


def remove_unwanted_msg(conversation):
    messages = []

    for msg in conversation:
        text = msg["content"].strip()

        if text.startswith("Welcome to your very own add a twist kitchen companion"):
            continue

        if text.startswith("View Recipe"):
            continue

        if msg["user"] == "user" and text.lower() == "help me decide":
            continue

        messages.append({
            "user": msg["user"],
            "content": text,
        })

    return messages


def effective_chunk_budget(previous_context: dict) -> int:
    
    previous_context_tokens = count_tokens(json.dumps(previous_context or {}))
    budget = MODEL_CONTEXT_WINDOW - FIXED_RESERVED_TOKENS - previous_context_tokens
    return max(budget, 2_000)


def create_token_chunks(messages: list[dict], max_chunk_tokens: int) -> list[list[dict]]:
    chunks = []
    current_chunk = []
    current_tokens = 0
    skipped_count = 0

    for message in messages:
        msg_token = count_tokens(message_to_text(message))

        if msg_token > max_chunk_tokens:
            user_id = message.get("user_id", "Unknown")
            logger.warning(
                f"Skipping message for user '{user_id}' — exceeds token limit "
                f"({msg_token} > {max_chunk_tokens} tokens)"
            )
            skipped_count += 1
            continue

        if current_tokens + msg_token > max_chunk_tokens:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = [message]
            current_tokens = msg_token
        else:
            current_chunk.append(message)
            current_tokens += msg_token

    if current_chunk:
        chunks.append(current_chunk)

    if skipped_count > 0:
        logger.warning(f"Skipped {skipped_count} oversized messages")

    return chunks


async def call_llm(data, brands, previous_context=None, max_retries=2) -> dict | None:
    
    if not previous_context:
        previous_context = {}
    
    prompt = (
        SMART_GROCERY_PROMPT.
        replace("__BOT_COMPANY_BRANDS__", json.dumps(brands, ensure_ascii=False))
        .replace("__PREVIOUS_CONTEXT__", json.dumps(previous_context or {}, ensure_ascii=False))
        .replace("__CONVERSATION_CHUNK__", json.dumps(data, ensure_ascii=False))
    )

    for attempt in range(max_retries + 1):
        
        llm_response = await llm.ainvoke(
            [
                SystemMessage(content=prompt)
            ]
        )

        content = llm_response.content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning(
                f"JSON parse failure on attempt {attempt + 1}/{max_retries + 1}. "
                f"Raw content: {content[:500]}"
            )
            continue

    logger.error("call_llm exhausted retries without valid JSON; caller must preserve previous state.")
    return None


async def smart_grocery_extraction():
    conversation_collection = get_collection(CONVERSATION_COLLECTION)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    last_month = today_start - timedelta(days=30)

    response = list(conversation_collection.find(
        {
            "created_at": {
                "$gte": last_month,
                "$lt": today_start,
            },
        },
        {
            "user_id": 1,
            "direction": 1,
            "content": 1,
            "created_at": 1,
            "_id": 0,
        },
    ).sort("created_at", 1))

    # print("conversation==========>",response)

    unique_message = remove_duplicates(response)
    group_users = group_by_user(unique_message)
    # print("group_user=============>",group_users, flush=True)
    
    recipe_brand_collection = get_collection(RECIPE_BRAND_COLLECTION)
    # print("recipe brand collection obtained", flush=True)
    for single_user in group_users.keys():
        user_messages = remove_unwanted_msg(group_users[single_user])

        if not user_messages:

            conversation_collection.update_many(
                {"user_id": single_user},
                {"$set": {"status": "processed"}},
            )
            continue


        brands = recipe_brand_collection.distinct("name")
        # print("brands:", brands, flush=True)
        
        brands_text = json.dumps(brands, ensure_ascii=False)

        chunk_budget = effective_chunk_budget(brands_text)
        chunks = create_token_chunks(user_messages, chunk_budget)

        if not chunks:
            continue

        working_profile = None
        merge_failed = False

        for i, chunk in enumerate(chunks):
            # role = "anchor" if i == 0 else "draft"
            result = await call_llm(chunk, brands=brands, previous_context=working_profile)

            if result is None:
                logger.error(
                    f"Skipping chunk {i} for user {single_user} due to repeated "
                    f"JSON parse failure. Preserving prior state for this user."
                )
                merge_failed = True
                continue

            working_profile = result

        # print(f"Final aggregated preference for {single_user}: {working_profile}")

        if merge_failed:
            logger.error(f"user_preference_extraction: partial merge failure for {single_user}")

        # print("working_profile===============>",working_profile)
        try:
            print("log 3========================>")
            smart_grocery_collection = get_collection(SMART_GROCERY_COLLECTION)
            smart_grocery_collection.update_one(
                {"user_id": single_user},
                {
                    "$set": {"smart_grocer_list": working_profile},
                    "$setOnInsert": {"cdate": datetime.utcnow()},
                },
                upsert=True,
            )

            conversation_collection.update_many(
                {"user_id": single_user},
                {"$set": {"grocery_status": "processed", "udate": datetime.utcnow()}},
            )
        except Exception as e:
            logger.error(f"ERROR persisting preferences for {single_user}: {e}")
            raise e