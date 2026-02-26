from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.graph.state import AgentState
from src.graph.prompts import WRITER_PROMPT
from src.graph.llms import get_llm
from src.utils.context import trim_history, flatten_for_text_llm


def writer_node(state: AgentState):
    messages = flatten_for_text_llm(trim_history(state.get("messages", [])))

    # Remove ToolMessages and AIMessages that contain tool_calls.
    # The Writer is a plain text LLM — passing tool-call messages causes
    # Groq to try calling non-existent tools, raising "Tool choice is none
    # but model called a tool".
    clean_messages = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            continue                          # skip tool results entirely
        if isinstance(msg, AIMessage) and msg.tool_calls:
            # Keep any plain text content the researcher produced but strip tool calls
            if msg.content and isinstance(msg.content, str) and msg.content.strip():
                clean_messages.append(AIMessage(content=msg.content))
            continue
        clean_messages.append(msg)

    # Fallback: if filtering removed everything, use only the last human message
    if not clean_messages:
        clean_messages = [m for m in messages if isinstance(m, HumanMessage)][-1:]

    llm = get_llm("logic-reasoning")
    prompt = ChatPromptTemplate.from_messages([
        ("system", WRITER_PROMPT),
        ("placeholder", "{messages}"),
    ])

    chain = prompt | llm
    response = chain.invoke({"messages": clean_messages})
    return {"messages": [response], "next_agent": "FINISH"}
