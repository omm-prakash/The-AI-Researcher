from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from src.graph.state import AgentState
from src.graph.prompts import RESEARCHER_PROMPT
from src.graph.llms import get_llm
from src.tools.search import internet_search_tool
from src.utils.context import trim_history, flatten_for_text_llm


def researcher_node(state: AgentState):
    """
    Researcher: Performs web research to answer the user's query.
    If an attachment subagent ran before this node, the pre-extracted
    attachment content is available in state['attachment_context'] and
    injected into the prompt directly — no tool calls needed for files.
    """
    print("\n[Researcher] Starting research...\n")

    messages = flatten_for_text_llm(trim_history(state.get("messages", [])))
    llm = get_llm("agentic-systems")

    # Build the attachment context block for the prompt
    attachment_context_raw = state.get("attachment_context", "")
    if attachment_context_raw:
        attachment_context = (
            "An attachment has already been processed and analyzed by a specialist subagent. "
            "Use the following extracted content to answer the user's query. "
            "You may also search the web to supplement this information if needed.\n\n"
            f"{attachment_context_raw}"
        )
    else:
        attachment_context = ""

    # Researcher only needs internet search — file tools are handled by subagents
    tools = [internet_search_tool]
    llm_with_tools = llm.bind_tools(tools)

    # Build the system message as a concrete SystemMessage object (not a tuple)
    # so that LangChain does NOT re-parse the pre-formatted text as a template.
    # This prevents ValueError when attachment_context contains literal { } characters.
    system_content = RESEARCHER_PROMPT.format(attachment_context=attachment_context)
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_content),
        ("placeholder", "{messages}"),
    ])

    chain = prompt | llm_with_tools
    response = chain.invoke({"messages": messages})

    print("[Researcher] Research complete.\n")
    return {"messages": [response], "next_agent": "Writer"}
