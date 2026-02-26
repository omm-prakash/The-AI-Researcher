from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import AgentState
from src.graph.prompts import SUPERVISOR_PROMPT
from src.graph.llms import get_llm
from src.utils.logger import get_logger

from pydantic import BaseModel, Field
from typing import Literal

logger = get_logger(__name__)

class Router(BaseModel):
    next_agent: Literal["Researcher", "Casual", "FINISH"] = Field(
        description="The next agent to route to depending on the task."
    )

from src.utils.context import trim_history, flatten_for_text_llm

def supervisor_node(state: AgentState):
    logger.info("── Supervisor ── routing decision started")
    members = ["Researcher", "Casual"]
    system_prompt = SUPERVISOR_PROMPT.format(members=", ".join(members))

    # Trim history then flatten multimodal content to strings for text-only LLM
    messages = flatten_for_text_llm(trim_history(state.get("messages", [])))
    logger.debug("Supervisor: %d messages in context", len(messages))

    # Use dynamic LLM routing
    llm = get_llm("logic-reasoning")
    structured_llm = llm.bind_tools([Router], tool_choice="Router").with_structured_output(Router)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}"),
    ])

    chain = prompt | structured_llm
    try:
        response = chain.invoke({"messages": messages})
        next_agent = response.next_agent
        logger.info("Supervisor → routing to: %s", next_agent)
    except Exception as e:
        error_str = str(e)
        logger.error("Supervisor routing failed: %s", error_str, exc_info=True)

        import re
        match = re.search(r'"failed_generation":\s*"([^"]*)"', error_str)
        failed_generation = match.group(1) if match else 'Sorry, I cannot answer this query.'

        from langchain_core.messages import RemoveMessage
        last_msg_id = messages[-1].id
        logger.warning("Supervisor: returning FINISH with error_response")
        return {
            "messages": [RemoveMessage(id=last_msg_id)],
            "next_agent": "FINISH",
            "error_response": failed_generation
        }

    return {"next_agent": next_agent, "error_response": ""}
