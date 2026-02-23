from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from src.graph.state import AgentState
from src.graph.prompts import SUPERVISOR_PROMPT
import os

from langchain_core.rate_limiters import InMemoryRateLimiter

# Pacing requests to 1 every 2 seconds to avoid Groq 429
rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.5,
    check_every_n_seconds=0.1,
    max_bucket_size=3,
)

def get_llm(messages=None):
    """
    Dynamically select the Groq model based on user prompt complexity.
    Uses ChatGroq strictly natively.
    """
    api_key = os.getenv("GROQ_API_KEY", "your_groq_api_key")
    
    # We will use two different models hosted by Groq natively
    model_name = "openai/gpt-oss-20b" # default for smaller requirements
    
    if messages:
        # Find the latest human message to gauge complexity
        user_messages = [m.content for m in messages if getattr(m, 'type', '') == 'human' or m.__class__.__name__ == 'HumanMessage']
        if user_messages:
            latest_prompt = user_messages[-1]
            # Heuristic for heavy duty tasks: length > 150 chars or contains specific keywords
            if len(latest_prompt) > 150 or any(k in latest_prompt.lower() for k in ["detailed", "research", "heavy", "complex"]):
                model_name = "openai/gpt-oss-120b"

    return ChatGroq(
        model=model_name, 
        api_key=api_key,
        max_retries=2,
        rate_limiter=rate_limiter
    )

from pydantic import BaseModel, Field
from typing import Literal

class Router(BaseModel):
    next_agent: Literal["Researcher", "Writer", "FINISH"] = Field(
        description="The next agent to route to depending on the task."
    )

from src.utils.context import trim_history

def supervisor_node(state: AgentState):
    members = ["Researcher", "Writer"]
    system_prompt = SUPERVISOR_PROMPT.format(members=", ".join(members))
    
    # Trim history to avoid 413 Payload Too Large and TPM rate limits
    messages = trim_history(state.get("messages", []))
    
    # Use dynamic LLM routing
    llm = get_llm(messages)
    structured_llm = llm.with_structured_output(Router)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}"),
    ])
    
    chain = prompt | structured_llm
    response = chain.invoke({"messages": messages})
    
    return {"next_agent": response.next_agent}
