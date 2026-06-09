from langgraph.graph import END, START, StateGraph

from graph.utils import AgentState


def start_node(state):
    print("working...")
    return state

def end_node(state):
    print("thank you...")
    return state

def build_graph():
    graph = StateGraph(AgentState)
    
    graph.add_node("start_node",start_node)
    graph.add_node("end_node", end_node)
    
    graph.add_edge(START,"start_node")
    graph.add_edge("start_node","end_node")
    graph.add_edge("end_node",END)