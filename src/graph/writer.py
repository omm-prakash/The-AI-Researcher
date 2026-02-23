from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import AgentState
from src.graph.prompts import WRITER_PROMPT
from src.graph.supervisor import get_llm

def writer_node(state: AgentState):
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", WRITER_PROMPT),
        ("placeholder", "{messages}"),
    ])
    
    chain = prompt | llm
    response = chain.invoke(state)
    return {"messages": [response]}
