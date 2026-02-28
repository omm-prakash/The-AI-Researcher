from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from src.graph.state import AgentState
from src.graph.nodes.supervisor import supervisor_node
from src.graph.nodes.researcher import researcher_node
from src.graph.nodes.casual import casual_node
from src.graph.nodes.guardrail import content_filter
from src.tools.search import tavily_search_tool, tavily_extract_tool


def _route_after_supervisor(state: AgentState) -> str:
    """
    Routing logic after the Supervisor decides.
    """
    next_agent = state.get("next_agent", "FINISH")
    attachment_type = state.get("attachment_type", "none")

    # Respect explicit termination
    if next_agent == "FINISH":
        return "FINISH"

    # If an attachment is present, always route to Researcher
    # because the Researcher now has the extraction tools.
    if attachment_type and attachment_type != "none":
        return "Researcher"
        
    return next_agent


def build_graph():
    builder = StateGraph(AgentState)

    # ── Core nodes ────────────────────────────────────────────────────────────
    builder.add_node("Guardrail", content_filter)
    builder.add_node("Supervisor", supervisor_node)
    builder.add_node("Researcher", researcher_node)
    builder.add_node("Casual", casual_node)

    from src.tools.file_extractors import pdf_extractor_tool, image_extractor_tool, audio_extractor_tool
    from src.tools.writer_tool import writer_tool
    
    # ── Internet search & file extraction tools node ──────
    builder.add_node("Tools", ToolNode([
        tavily_search_tool, 
        tavily_extract_tool,
        pdf_extractor_tool,
        image_extractor_tool,
        audio_extractor_tool,
        writer_tool
    ]))

    # ── Edges ─────────────────────────────────────────────────────────────────

    # Entry point → Guardrail
    builder.add_edge(START, "Guardrail")

    # Guardrail either passes to Supervisor or terminates
    builder.add_conditional_edges(
        "Guardrail",
        lambda state: state["next_agent"],
        {
            "Supervisor": "Supervisor",
            "FINISH": END,
        },
    )

    # Supervisor → [Researcher | Casual | END]
    builder.add_conditional_edges(
        "Supervisor",
        _route_after_supervisor,
        {
            "Researcher": "Researcher",
            "Casual": "Casual",
            "FINISH": END,
        },
    )

    # Researcher → Tools (if web search called) or → END
    builder.add_conditional_edges(
        "Researcher",
        tools_condition,
        {
            "tools": "Tools",
            END: END,
        },
    )

    # Tools feed back into Researcher for follow-up reasoning
    builder.add_edge("Tools", "Researcher")

    # Terminal edges
    builder.add_edge("Casual", END)

    return builder
