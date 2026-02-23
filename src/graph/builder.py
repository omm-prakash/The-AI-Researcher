from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from src.graph.state import AgentState
from src.graph.supervisor import supervisor_node
from src.graph.researcher import researcher_node
from src.graph.writer import writer_node
from src.graph.casual import casual_node
from src.graph.guardrail import content_filter
from src.tools.search import internet_search_tool

def build_graph():
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("Supervisor", supervisor_node)
    builder.add_node("Guardrail", content_filter)
    builder.add_node("Researcher", researcher_node)
    builder.add_node("Writer", writer_node)
    builder.add_node("Casual", casual_node)
    
    # We need a tool execution node for the researcher
    # builder.add_node("Tools", ToolNode([internet_search_tool]))
    
    # Add edges
    builder.add_edge(START, "Guardrail")
    
    # Guardrail either passes to Supervisor or terminates
    builder.add_conditional_edges(
        "Guardrail",
        lambda state: state["next_agent"],
        {
            "Supervisor": "Supervisor",
            "FINISH": END
        }
    )
    
    # The supervisor determines the next action
    builder.add_conditional_edges(
        "Supervisor",
        lambda state: state["next_agent"],
        {
            "Researcher": "Researcher",
            "Casual": "Casual",
            "FINISH": END
        }
    )
    
    # Researcher output goes to tools if a tool was called, else back to supervisor
    # builder.add_conditional_edges(
    #     "Researcher",
    #     tools_condition,
    #     {
    #         "tools": "Tools",
    #         END: "Supervisor"
    #     }
    # )
    
    # Tools node returns results back to researcher agent
    # builder.add_edge("Tools", "Researcher")
    
    # Writers return to supervisor
    # builder.add_edge("Researcher", "Supervisor")
    builder.add_edge("Casual", END)
    builder.add_edge("Researcher", "Writer")
    builder.add_edge("Writer", END)
    # agent = builder.compile()
    
    return builder
