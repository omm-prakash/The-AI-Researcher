from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import AgentState
from src.graph.prompts import CASUAL_PROMPT
from src.graph.llms import get_llm
from src.utils.context import trim_history
from src.utils.logger import get_logger

logger = get_logger(__name__)


def casual_node(state: AgentState):
    logger.info("── CasualAgent ── handling casual conversation")
    messages = trim_history(state.get("messages", []))
    logger.debug("CasualAgent: %d messages in context", len(messages))

    llm = get_llm("efficiency-edge", temperature=0.6)
    prompt = ChatPromptTemplate.from_messages([
        ("system", CASUAL_PROMPT),
        ("placeholder", "{messages}"),
    ])

    try:
        chain = prompt | llm
        response = chain.invoke({"messages": messages})
        logger.info("CasualAgent: response generated → FINISH")
    except Exception as e:
        logger.error("CasualAgent: LLM call failed: %s", e, exc_info=True)
        raise

    return {"messages": [response], "next_agent": "FINISH"}
