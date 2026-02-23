from langgraph.graph import StateGraph, START, END
from src.graph.state import AgentState
from src.graph.supervisor import supervisor_node
from src.graph.researcher import researcher_node
from src.graph.writer import writer_node

def build_graph():
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("Supervisor", supervisor_node)
    builder.add_node("Researcher", researcher_node)
    builder.add_node("Writer", writer_node)
    
    # Add edges
    builder.add_edge(START, "Supervisor")
    
    # The supervisor determines the next agent
    builder.add_conditional_edges(
        "Supervisor",
        lambda state: state["next_agent"],
        {
            "Researcher": "Researcher",
            "Writer": "Writer",
            "FINISH": END
        }
    )
    
    # Workers report back to the supervisor
    builder.add_edge("Researcher", "Supervisor")
    builder.add_edge("Writer", "Supervisor")
    
    return builder
