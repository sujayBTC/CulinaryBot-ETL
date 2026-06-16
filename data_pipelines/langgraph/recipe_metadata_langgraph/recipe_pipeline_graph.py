import asyncio
from datetime import datetime
from typing import List, Literal, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from data_pipelines.core.config import MONGO_DB
from data_pipelines.langgraph.recipe_metadata_langgraph.fetch_recipe_node_recipe import fetch_recipe_node_for_recipe
from data_pipelines.langgraph.recipe_metadata_langgraph.recipe_llm_process import recipe_llm_process
from data_pipelines.langgraph.recipe_metadata_langgraph.recipe_metadata_store import recipe_metadata_store
from data_pipelines.langgraph.state_manager import State


def build_graph() -> StateGraph[State]:
    graph = StateGraph(State)

    graph.set_node_defaults(retry_policy=RetryPolicy(max_attempts=3))
    # nodes
    graph.add_node("fetch_recipes", fetch_recipe_node_for_recipe)
    graph.add_node("recipe_metadata_generator", recipe_llm_process)
    graph.add_node("store_recipe_data", recipe_metadata_store)

    # linear flow: start -> fetch -> process
    graph.add_edge(START, "fetch_recipes")
    graph.add_edge("fetch_recipes", "recipe_metadata_generator")
    graph.add_edge("recipe_metadata_generator", END)
    
    return graph
