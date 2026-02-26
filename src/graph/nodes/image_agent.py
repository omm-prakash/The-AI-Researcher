import os
import base64
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from src.graph.state import AgentState
from src.graph.prompts import IMAGE_AGENT_PROMPT
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Vision models to try in order — scout is widely validated, maverick as fallback
VISION_MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
]

MIME_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


def image_agent_node(state: AgentState):
    """
    ImageAgent: Analyzes an image attachment using ChatGroq directly
    (bypassing the get_llm() with_fallbacks() wrapper, which interferes with
    multimodal content delivery), then stores the analysis in
    state['attachment_context'] for the Researcher.
    """
    logger.info("── ImageAgent ── starting image analysis")

    attachment_path = state.get("attachment_path", "")
    messages = state.get("messages", [])

    # Extract the latest user query for focused analysis
    user_query = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            user_query = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    if not attachment_path or not os.path.exists(attachment_path):
        logger.warning("ImageAgent: file not found at '%s'", attachment_path)
        return {"attachment_context": "Image file could not be found or read."}

    try:
        with open(attachment_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        logger.error("ImageAgent: failed to read image: %s", e, exc_info=True)
        return {"attachment_context": f"Failed to read image file: {str(e)}"}

    ext = attachment_path.lower().rsplit(".", 1)[-1]
    mime_type = MIME_MAP.get(ext, "image/jpeg")
    system_text = IMAGE_AGENT_PROMPT.format(user_query=user_query)

    api_key = os.getenv("GROQ_API_KEY")
    extracted = None
    last_error = None

    for model in VISION_MODELS:
        try:
            logger.info("ImageAgent: trying vision model '%s'", model)
            # Use ChatGroq directly — NOT via get_llm() — to avoid with_fallbacks()
            # wrapper transforming the multimodal HumanMessage content.
            llm = ChatGroq(model=model, api_key=api_key, max_retries=0)
            message = HumanMessage(
                content=[
                    {"type": "text", "text": system_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{encoded_string}",
                        },
                    },
                ]
            )
            response = llm.invoke([message])
            extracted = response.content.strip()
            logger.info("ImageAgent: success with model '%s'", model)
            break
        except Exception as e:
            logger.warning("ImageAgent: model '%s' failed (%s: %s) — trying next", model, type(e).__name__, e)
            last_error = e
            continue

    if extracted is None:
        error_msg = str(last_error) if last_error else "All vision models failed"
        logger.error("ImageAgent: all vision models exhausted — %s", error_msg)
        return {"attachment_context": f"Image analysis failed: {error_msg}"}

    context_block = (
        "[Image Attachment Analysis]\n"
        "The following analysis was performed on the attached image "
        "in relation to the user's query:\n\n"
        f"{extracted}"
    )

    logger.info("ImageAgent: analysis complete → attachment_context set")
    return {"attachment_context": context_block}
