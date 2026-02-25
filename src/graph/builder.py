from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from src.graph.state import AgentState
from src.graph.nodes.supervisor import supervisor_node
from src.graph.nodes.researcher import researcher_node
from src.graph.nodes.writer import writer_node
from src.graph.nodes.casual import casual_node
from src.graph.nodes.guardrail import content_filter
from src.graph.nodes.pdf_agent import pdf_agent_node
from src.graph.nodes.image_agent import image_agent_node
from src.graph.nodes.audio_agent import audio_agent_node
from src.tools.search import internet_search_tool


def _route_after_supervisor(state: AgentState) -> str:
    """
    After the Supervisor decides to use the Researcher, inspect whether
    an attachment was uploaded and route to the matching subagent first.
    If the Supervisor chose Casual or FINISH, pass that through directly.
    """
    next_agent = state.get("next_agent", "FINISH")
    attachment_type = state.get("attachment_type", "none")

    # If supervisor decided to use Researcher AND there is an attachment,
    # delegate to the appropriate specialist subagent first.
    if next_agent == "Researcher" and attachment_type != "none":
        attachment_routes = {
            "pdf": "PDFAgent",
            "image": "ImageAgent",
            "audio": "AudioAgent",
        }
        return attachment_routes.get(attachment_type, "Researcher")

    return next_agent


def build_graph():
    builder = StateGraph(AgentState)

    # ── Core nodes ────────────────────────────────────────────────────────────
    builder.add_node("Guardrail", content_filter)
    builder.add_node("Supervisor", supervisor_node)
    builder.add_node("Researcher", researcher_node)
    builder.add_node("Writer", writer_node)
    builder.add_node("Casual", casual_node)

    # ── Attachment subagent nodes ─────────────────────────────────────────────
    builder.add_node("PDFAgent", pdf_agent_node)
    builder.add_node("ImageAgent", image_agent_node)
    builder.add_node("AudioAgent", audio_agent_node)

    # ── Internet search tool node (Researcher may still call web search) ──────
    builder.add_node("Tools", ToolNode([internet_search_tool]))

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

    # Supervisor → [PDFAgent | ImageAgent | AudioAgent | Researcher | Casual | END]
    builder.add_conditional_edges(
        "Supervisor",
        _route_after_supervisor,
        {
            "PDFAgent": "PDFAgent",
            "ImageAgent": "ImageAgent",
            "AudioAgent": "AudioAgent",
            "Researcher": "Researcher",
            "Casual": "Casual",
            "FINISH": END,
        },
    )

    # Each subagent hands off directly to the Researcher once extraction is done
    builder.add_edge("PDFAgent", "Researcher")
    builder.add_edge("ImageAgent", "Researcher")
    builder.add_edge("AudioAgent", "Researcher")

    # Researcher → Tools (if web search called) or → Writer
    builder.add_conditional_edges(
        "Researcher",
        tools_condition,
        {
            "tools": "Tools",
            END: "Writer",
        },
    )

    # Tools feed back into Researcher for follow-up reasoning
    builder.add_edge("Tools", "Researcher")

    # Terminal edges
    builder.add_edge("Casual", END)
    builder.add_edge("Writer", END)

    return builder
