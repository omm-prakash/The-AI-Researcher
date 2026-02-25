import os
import base64
from langchain_core.messages import HumanMessage
from src.graph.state import AgentState
from src.graph.prompts import IMAGE_AGENT_PROMPT
from src.graph.llms import get_llm


def image_agent_node(state: AgentState):
    """
    ImageAgent: Dedicated subagent that analyzes an image attachment using a
    vision-capable LLM and writes its findings to state['attachment_context'].
    """
    print("\n[ImageAgent] Starting image analysis...\n")

    attachment_path = state.get("attachment_path", "")
    messages = state.get("messages", [])

    # Extract the user's latest query for focused analysis
    user_query = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            user_query = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    if not attachment_path or not os.path.exists(attachment_path):
        print(f"[ImageAgent] File not found at: {attachment_path}")
        return {"attachment_context": "Image file could not be found or read."}

    try:
        with open(attachment_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"[ImageAgent] Failed to read image: {e}")
        return {"attachment_context": f"Failed to read image file: {str(e)}"}

    # Determine MIME type from extension
    ext = attachment_path.lower().rsplit(".", 1)[-1]
    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                "gif": "image/gif", "webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")

    try:
        llm = get_llm("multimodal-moe")

        # Build the system instruction as a text part, attach image
        system_text = IMAGE_AGENT_PROMPT.format(user_query=user_query)

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
    except Exception as e:
        print(f"[ImageAgent] LLM analysis failed: {e}")
        return {"attachment_context": f"Image analysis failed: {str(e)}"}

    context_block = (
        f"[Image Attachment Analysis]\n"
        f"The following analysis was performed on the attached image in relation to the user's query:\n\n"
        f"{extracted}"
    )

    print("[ImageAgent] Analysis complete.\n")
    return {"attachment_context": context_block}
