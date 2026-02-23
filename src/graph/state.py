from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    State for the multi-agent graph.
    - messages: all the messages in the conversation
    - next_agent: the next agent to route to, determined by the supervisor
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_agent: str
