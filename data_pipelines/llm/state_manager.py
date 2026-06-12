from typing import List, Literal, TypedDict
from uuid import uuid4

class State(TypedDict, total=False):
    execution_id: uuid4
    current_chunk: List[dict]
    total_chunks: int
    current_chunk_index: int
    current_chunk_tokens: int
    processed_data: List[str]
