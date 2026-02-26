import logging
from src.graph.state import AgentState
from src.graph.llms import get_llm
from langchain_core.messages import AIMessage, RemoveMessage, HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Layer 1 – fast deterministic keyword filter
# ---------------------------------------------------------------------------
BANNED_KEYWORDS = [
    "violent", "violence", "kill", "murder", "blood", "gore", "attack",
    "sex", "sexual", "porn", "pornography", "nsfw", "nude", "nudity",
]

# Llama Guard returns "safe" or "unsafe\n<category>" — we look for this prefix
_UNSAFE_PREFIX = "unsafe"

# System prompt for Llama Guard / prompt-guard models
_GUARD_SYSTEM = (
    "You are a safety classifier. "
    "Evaluate the following user message and respond with exactly one word: "
    "'safe' if the content is appropriate, or 'unsafe' if it contains harmful, "
    "sensitive, explicit, or policy-violating content."
)

_BLOCKED_RESPONSE = (
    "I cannot process requests containing inappropriate or sensitive content. "
    "Please rephrase your query."
)


def _extract_text(message) -> str:
    """Return lowercased plain text from a human message (handles multimodal)."""
    raw = message.content
    if isinstance(raw, list):
        return " ".join(
            part.get("text", "") for part in raw if isinstance(part, dict)
        ).lower()
    return str(raw).lower()


def _block(message):
    """Build the state patch that blocks the request."""
    return {
        "messages": [RemoveMessage(id=message.id)],
        "next_agent": "FINISH",
        "error_response": _BLOCKED_RESPONSE,
    }


def content_filter(state: AgentState):
    """
    Two-layer guardrail that filters sensitive / harmful prompts.

    Layer 1 – Keyword filter  (fast, zero-cost, deterministic)
    Layer 2 – Llama Guard LLM (meta-llama/llama-guard-4-12b via Groq)
              called only when the keyword check passes.
    """
    if not state.get("messages"):
        return {"next_agent": "Supervisor"}

    last_msg = state["messages"][-1]

    # Only inspect human messages
    msg_type = getattr(last_msg, "type", "") or last_msg.__class__.__name__
    if msg_type not in ("human", "HumanMessage"):
        return {"next_agent": "Supervisor"}

    content = _extract_text(last_msg)

    # ------------------------------------------------------------------
    # Layer 1: keyword check
    # ------------------------------------------------------------------
    for keyword in BANNED_KEYWORDS:
        if keyword in content:
            print(f"[Guardrail] Blocked by keyword: '{keyword}'")
            return _block(last_msg)

    # ------------------------------------------------------------------
    # Layer 2: LLM safety model (Llama Guard 4 / Prompt Guard)
    # ------------------------------------------------------------------
    try:
        safety_llm = get_llm("safety-security")
        response = safety_llm.invoke([
            SystemMessage(content=_GUARD_SYSTEM),
            HumanMessage(content=content),
        ])
        verdict = response.content.strip().lower()
        logger.debug("[Guardrail] Safety LLM verdict: %s", verdict)

        if verdict.startswith(_UNSAFE_PREFIX):
            print(f"[Guardrail] Blocked by safety LLM — verdict: '{verdict}'")
            return _block(last_msg)

    except Exception as exc:
        # If the safety LLM fails, log and fall through (fail open)
        logger.warning("[Guardrail] Safety LLM unavailable, skipping: %s", exc)

    # Clean — proceed to the supervisor
    return {"next_agent": "Supervisor"}
