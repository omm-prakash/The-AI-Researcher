from src.graph.state import AgentState
from langchain_core.messages import AIMessage, RemoveMessage

# A basic list of banned keywords for deterministic moderation
banned_keywords = [
    "violent", "violence", "kill", "murder", "blood", "gore", "attack",
    "sex", "sexual", "porn", "pornography", "nsfw", "nude", "nudity"
]

def content_filter(state: AgentState):
    """
    Deterministic guardrail: Block requests containing banned keywords.
    """
    # Get the latest user message
    if not state.get("messages"):
        return {"next_agent": "Supervisor"}

    first_message = state["messages"][-1]
    
    # Check if the latest message is from a human
    if getattr(first_message, 'type', '') != 'human' and first_message.__class__.__name__ != 'HumanMessage':
        return {"next_agent": "Supervisor"}

    content = first_message.content.lower()

    # Check for banned keywords
    for keyword in banned_keywords:
        if keyword in content:
            # Block execution, remove the violating message, and route to FINISH
            remove_cmd = RemoveMessage(id=first_message.id)
            blocked_msg = "I cannot process requests containing inappropriate or sensitive content. Please rephrase your query."
            return {
                "messages": [remove_cmd],
                "next_agent": "FINISH",
                "error_response": blocked_msg
            }

    # If clean, proceed to the supervisor
    return {"next_agent": "Supervisor"}
