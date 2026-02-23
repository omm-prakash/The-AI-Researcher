from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import AgentState
from src.graph.prompts import RESEARCHER_PROMPT
from src.graph.llms import get_llm
from src.tools.search import internet_search_tool

from src.utils.context import trim_history

def researcher_node(state: AgentState):
    messages = trim_history(state.get("messages", []))
    llm = get_llm("agentic-systems")
    from src.tools.pdf_reader import read_pdf_tool
    
    attachment_type = state.get("attachment_type", "none")
    attachment_path = state.get("attachment_path")
    
    attachment_context = ""
    if attachment_type != "none" and attachment_path:
        attachment_context = f"The user has attached a '{attachment_type}' file located at: {attachment_path}.\nYou must use your tools to extract and read this file."

    # Provide the custom tools
    avialable_tools = {
        'pdf': read_pdf_tool,
        'image': read_image_tool,
        'audio': read_audio_tool,
        'internet': internet_search_tool
    }

    tools = [internet_search_tool]
    if attachment_type != "none":
        tools.append(avialable_tools[attachment_type])

    llm_with_tools = llm.bind_tools(tools)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", RESEARCHER_PROMPT.format(attachment_context=attachment_context)),
        ("placeholder", "{messages}"),
    ])
    
    chain = prompt | llm_with_tools
    response = chain.invoke({"messages": messages})
    return {"messages": [response], "next_agent": "Writer"}
