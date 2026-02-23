from src.graph.supervisor import *
from src.graph.state import AgentState
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
load_dotenv()

state = {"messages": [HumanMessage(content="Hello, what is the weather in Tokyo today?")], "next_agent": ""}
print(supervisor_node(state))
