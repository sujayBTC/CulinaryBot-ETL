from typing import TypedDict, List, Literal
import asyncio

from langgraph.graph import StateGraph, START
from langgraph.constants import END

from data_pipelines.graph.node_functions.fetch_recipe_node import fetch_recipe_node
from utils.utils import State


def build_graph() -> StateGraph[State]:
    graph = StateGraph(State)

    # nodes
    graph.add_node("fetch_recipes", fetch_recipe_node)

    # linear flow: start -> fetch -> process
    graph.add_edge(START, "fetch_recipes")

    return graph


if __name__ == "__main__":
    # Quick local test: run the graph end-to-end and print final state.
    g = build_graph().compile()

    result = asyncio.run(g.ainvoke({}))
    print("Final state:", result)
