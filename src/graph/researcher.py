from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from src.graph.state import AgentState
from src.graph.prompts import RESEARCHER_PROMPT
from src.graph.supervisor import get_llm

def researcher_node(state: AgentState):
    llm = get_llm()
    # Provide the research tool
    tools = [TavilySearchResults(max_results=3)]
    llm_with_tools = llm.bind_tools(tools)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", RESEARCHER_PROMPT),
        ("placeholder", "{messages}"),
    ])
    
    chain = prompt | llm_with_tools
    response = chain.invoke(state)
    return {"messages": [response]}
