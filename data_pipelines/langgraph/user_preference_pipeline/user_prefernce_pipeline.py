import json
import tiktoken

from datetime import datetime, timedelta
from collections import defaultdict
from logger import logger

from langchain_core.messages import HumanMessage, SystemMessage
from data_pipelines.llm.model import llm
from data_pipelines.llm.prompt import SYSTEM_PROMPT, USER_PREFERENCE_PROMPT, USER_PREFERENCE_USER_PROMPT

from data_pipelines.db.mongo import get_collection

CONVERSATION_COLLECTION = 'conversations'
USER_PREFERENCE_KEYWORD = 'user_preference_keyword'

MODEL_NAME = "gpt-4o"
MODEL_CONTEXT_WINDOW = 128_000
RESERVED_TOKENS = (
    5_000  # system prompt
    + 20_000  # existing keyword dictionary
    + 5_000  # expected response
    + 8_000  # safety buffer
)
MAX_CHUNK_TOKENS = MODEL_CONTEXT_WINDOW - RESERVED_TOKENS

try:
    encoder = tiktoken.encoding_for_model(MODEL_NAME)
except KeyError:
    encoder = tiktoken.get_encoding("cl100k_base")


def message_to_text(msg: dict) -> str:
    return f"[{msg['user']}] {msg['content']}"


def count_tokens(text: str) -> int:
    return len(encoder.encode(text))


def remove_duplicates(messages):
    seen = set()
    unique = []

    for m in messages:
        key = (m["user_id"], m["content"].lower())
        if key not in seen:
            seen.add(key)
            unique.append(m)

    return unique


def group_by_user(messages):
    user_map = defaultdict(list)

    for m in messages:
        user_map[m["user_id"]].append({
        "user":"user" if m["direction"] == "inbound" else "bot",
        "content": m["content"]
        })

    return user_map


def remove_unwanted_msg(conversation):
    messages = []

    for msg in conversation:
        text = msg["content"].strip()

        # Remove welcome/greeting message
        if text.startswith("Welcome to your very own add a twist kitchen companion"):
            continue

        # Remove "View Recipe" commands
        if text.startswith("View Recipe"):
            continue

        # Optional: remove "help me decide"
        if msg["user"] == "user" and text.lower() == "help me decide":
            continue

        messages.append({
            "user": msg["user"],
            "content": text
        })
    
    return messages
        
        
def create_token_chunks(messages: list[dict]) -> list[list[dict]]:
    chunks = []
    current_chunk = []
    current_tokens = 0
    skipped_count = 0

    for message in messages:
        msg_token = count_tokens(message_to_text(message))

        if msg_token > MAX_CHUNK_TOKENS:
            user_id = message.get("user_id", "Unknown")
            print(
                f"Skipping recipe '{user_id}' "
                f"because it exceeds token limit "
                f"({msg_token} > {MAX_CHUNK_TOKENS} tokens)"
            )
            skipped_count += 1
            continue

        if current_tokens + msg_token > MAX_CHUNK_TOKENS:
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
        print(f"Skipped {skipped_count} oversized recipes")

    return chunks


async def call_llm(data, previous_context=None) -> dict:
    
    if not previous_context:
        previous_context = {}

    data = {"conversation":data}
    
    llm_response = await llm.ainvoke(
        [
            SystemMessage(content=USER_PREFERENCE_PROMPT),
            HumanMessage(content=USER_PREFERENCE_USER_PROMPT.format(previous_profile=previous_context,conversation=json.dumps(data))),
        ]
    )
    
    content = llm_response.content.strip()
    
    try:
        final_llm = json.loads(llm_response.content)
        
    except json.JSONDecodeError:
        print(content)
        final_llm = {}
    
    return final_llm


async def user_preference_extraction():
    
    conversation_collection = get_collection(CONVERSATION_COLLECTION)
    today_start = datetime.utcnow().replace(month=7, day=8,hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)
    
    response = list(conversation_collection.find(
        {
            # "created_at": {
            #     "$gte": today_start.isoformat(),
            #     "$lt": tomorrow_start.isoformat(),
            # },
            # "status":{
            #     "$ne": "processed"
            # }
        },
        {
            "user_id": 1,
            "direction": 1,
            "content": 1,
            "_id": 0,
        },
    ))
    
    print("response==========>",response)
    
    unique_message = remove_duplicates(response)
    
    group_users = group_by_user(unique_message)
    
    for single_user in group_users.keys():
        
        user_messages = remove_unwanted_msg(group_users[single_user])
        
        chunks = create_token_chunks(user_messages)
        
        print("chunk len======>",len(chunks))
        
        final_preference = None 
        
        for chunk in chunks:
            final_preference = await call_llm(chunk, previous_context=final_preference)
    
        print(f"Final aggregated preference for {single_user}: {final_preference}")

        
        user_preference_collection = get_collection(USER_PREFERENCE_KEYWORD)
        
        try:
            user_preference_collection.update_one(
                {"user_id": single_user},
                {"$set": {"user_preferences": final_preference},
                "$setOnInsert": {
                    "cdate": datetime.utcnow()
                }},
                upsert=True,
            )
            conversation_collection.update_many(
                {"user_id": single_user},
                {"$set": {"status": "processed"},
                "$setOnInsert": {
                    "udate": datetime.utcnow()
                }},
                upsert=True,
            )
        except Exception as e:
            print(f"ERROR: {e}")
    
    # triger send_keyword to application logic