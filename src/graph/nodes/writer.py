from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.graph.state import AgentState
from src.graph.prompts import WRITER_PROMPT
from src.graph.llms import get_llm
from src.utils.context import trim_history, flatten_for_text_llm
from src.utils.logger import get_logger

logger = get_logger(__name__)


def writer_node(state: AgentState):
    logger.info("── Writer ── composing final response")
    # messages = flatten_for_text_llm(trim_history(state.get("messages", [])))

    # Remove ToolMessages and AIMessages that contain tool_calls.
    # The Writer is a plain text LLM — passing tool-call messages causes
    # Groq to try calling non-existent tools.
    # clean_messages = []
    clean_messages = [state.get("messages", None)[-1]]  
    print('clean_messages', clean_messages)
    # for msg in messages:
    #     if isinstance(msg, ToolMessage):
    #         continue
    #     if isinstance(msg, AIMessage) and msg.tool_calls:
    #         if msg.content and isinstance(msg.content, str) and msg.content.strip():
    #             clean_messages.append(AIMessage(content=msg.content))
    #         continue
    #     clean_messages.append(msg)

    # if not clean_messages:
    #     logger.warning("Writer: all messages filtered out — falling back to last HumanMessage")
    #     clean_messages = [m for m in messages if isinstance(m, HumanMessage)][-1:]

    logger.debug("Writer: %d clean messages passed to LLM", len(clean_messages))

    llm = get_llm("logic-reasoning")
    prompt = ChatPromptTemplate.from_messages([
        ("system", WRITER_PROMPT),
        # ("placeholder", "{messages}"),
    ])

    print('clean_messages', len(clean_messages))
    try:
        chain = prompt | llm
        response = chain.invoke({"messages": clean_messages})
        logger.info("Writer: response composed → FINISH")
    except Exception as e:
        logger.error("Writer: LLM call failed: %s", e, exc_info=True)
        raise

    return {"messages": [response], "next_agent": "FINISH"}
