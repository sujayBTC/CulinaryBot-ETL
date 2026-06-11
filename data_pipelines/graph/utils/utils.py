from typing import TypedDict, List, Literal

class State(TypedDict, total=False):
    current_chunk: List[dict]
    total_chunks: int
    current_chunk_index: int
    processed_data: List[dict]
