from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage
import os
from dotenv import load_dotenv

load_dotenv()

class Router(BaseModel):
    next_agent: Literal["Researcher", "Writer", "Casual", "FINISH"] = Field(
        description="The next agent to route to depending on the task."
    )

llm = ChatGroq(model="openai/gpt-oss-20b", api_key=os.getenv("GROQ_API_KEY"))

messages = [
    HumanMessage(content="Hello"),
    AIMessage(content="I cannot process requests containing inappropriate or sensitive content. Please rephrase your query."),
    HumanMessage(content="Find me latest news on quantum computing.")
]

try:
    print("Testing standard with_structured_output()...")
    # By default, method="function_calling" is used. Let's see if we can force tool_choice
    structured_llm = llm.with_structured_output(Router)
    res = structured_llm.invoke(messages)
    print("SUCCESS:", res)
except Exception as e:
    print("FAILED:", e)

try:
    print("\nTesting with_structured_output() with explicit bind_tools...")
    # Does this work?
    structured_llm2 = llm.with_structured_output(Router)
    # Actually let's manually bind and parse
    llm_bound = llm.bind_tools([Router], tool_choice="Router")
    res2 = llm_bound.invoke(messages)
    print("SUCCESS RAW:", res2.tool_calls)
except Exception as e:
    print("FAILED:", e)
