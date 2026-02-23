from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import AgentState
from src.graph.prompts import RESEARCHER_PROMPT
from src.graph.supervisor import get_llm
from src.tools.search import internet_search_tool

from src.utils.context import trim_history

def researcher_node(state: AgentState):
    messages = trim_history(state.get("messages", []))
    llm = get_llm(messages)
    # Provide the custom internet search tool
    # tools = [internet_search_tool]
    # llm_with_tools = llm.bind_tools(tools)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", RESEARCHER_PROMPT),
        ("placeholder", "{messages}"),
    ])
    
    # chain = prompt | llm_with_tools
    chain = prompt | llm
    response = chain.invoke({"messages": messages})
    return {"messages": [response]}
