from typing import Annotated, Sequence, TypedDict, Literal, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict, total=False):
    """
    State for the multi-agent graph.
    - messages: all the messages in the conversation
    - next_agent: the next agent to route to, determined by the supervisor
    - error_response: an optional string to return directly to the user without adding to the database context
    - attachment_type: type of file attached by the user (pdf, image, audio, or none)
    - attachment_path: filesystem path to the uploaded attachment
    - attachment_context: pre-extracted content written by the attachment subagent (PDFAgent / ImageAgent / AudioAgent)
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_agent: str
    error_response: str
    attachment_type: Literal["pdf", "image", "audio", "none"]
    attachment_path: Optional[str]
    attachment_context: str
    
