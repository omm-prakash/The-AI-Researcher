from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import AgentState
from src.graph.prompts import CASUAL_PROMPT
from src.graph.llms import get_llm
from src.utils.context import trim_history

def casual_node(state: AgentState):
    messages = trim_history(state.get("messages", []))
    llm = get_llm("efficiency-edge")
    prompt = ChatPromptTemplate.from_messages([
        ("system", CASUAL_PROMPT),
        ("placeholder", "{messages}"),
    ])

    # print('\n', 'Casual Node')
    # for msg in messages:
    #     print(msg.content)
    # print()
    
    chain = prompt | llm
    response = chain.invoke({"messages": messages})
    return {"messages": [response], "next_agent": "FINISH"}
