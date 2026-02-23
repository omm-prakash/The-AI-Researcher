from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from src.graph.state import AgentState
from src.graph.prompts import SUPERVISOR_PROMPT
import os

from langchain_groq import ChatGroq

def get_llm():
    # Initialize the Groq model
    api_key = os.getenv("GROQ_API_KEY", "your_groq_api_key")
    # For example using llama3-8b-8192 or mixtral
    return ChatGroq(model="llama3-8b-8192", api_key=api_key)

def supervisor_node(state: AgentState):
    members = ["Researcher", "Writer"]
    system_prompt = SUPERVISOR_PROMPT.format(members=", ".join(members))
    
    # Use LLM to decide the next agent
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}"),
    ])
    
    # We can bind a tool to force JSON structural output, or just parse string
    # For simplicity, let's use a structured output router if available,
    # or just parse the text.
    
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"]})
    
    # very simple parsing
    next_agent = response.content.strip()
    if "Researcher".lower() in next_agent.lower():
        return {"next_agent": "Researcher"}
    elif "Writer".lower() in next_agent.lower():
        return {"next_agent": "Writer"}
    else:
        return {"next_agent": "FINISH"}
