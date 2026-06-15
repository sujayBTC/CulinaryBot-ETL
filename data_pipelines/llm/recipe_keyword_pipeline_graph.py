import asyncio
from datetime import datetime
from typing import List, Literal, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from data_pipelines.core.config import MONGO_DB
from data_pipelines.llm.node_functions.chunk_orchestrator import chunk_orchestrator
from data_pipelines.llm.node_functions.fetch_recipe_node import fetch_recipe_node
from data_pipelines.llm.node_functions.generate_keywords import generate_keywords
from data_pipelines.llm.node_functions.store_keyword import store_keywords
from data_pipelines.llm.state_manager import State


def build_graph() -> StateGraph[State]:
    graph = StateGraph(State)

    graph.set_node_defaults(retry_policy=RetryPolicy(max_attempts=3))
    # nodes
    graph.add_node("fetch_recipes", fetch_recipe_node)
    graph.add_node("chunk_orchestrator", chunk_orchestrator)
    graph.add_node("generate_keywords", generate_keywords)
    graph.add_node("store_keywords", store_keywords)

    # linear flow: start -> fetch -> process
    graph.add_edge(START, "fetch_recipes")
    graph.add_edge("fetch_recipes", "chunk_orchestrator")
    graph.add_edge("chunk_orchestrator", END)
    
    return graph
