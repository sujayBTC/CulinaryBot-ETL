from langgraph.types import Command


def chunk_orchestrator(state):
    current_idx = state["current_chunk_index"]
    total_chunks = len(state["chunks"])

    if current_idx < total_chunks:
        return Command(goto="fetch_recipe_node")

    return Command(goto="finalize_keywords")
