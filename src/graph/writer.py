from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import AgentState
from src.graph.prompts import WRITER_PROMPT
from src.graph.supervisor import get_llm

from src.utils.context import trim_history

def writer_node(state: AgentState):
    messages = trim_history(state.get("messages", []))
    llm = get_llm(messages)
    prompt = ChatPromptTemplate.from_messages([
        ("system", WRITER_PROMPT),
        ("placeholder", "{messages}"),
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": messages})
    return {"messages": [response]}
