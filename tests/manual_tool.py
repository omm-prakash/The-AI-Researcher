from src.graph.researcher import *
from src.graph.state import AgentState
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
load_dotenv()

state = {"messages": [HumanMessage(content="Search the internet for the weather in Tokyo today in 2026.")], "next_agent": ""}
print(researcher_node(state))
