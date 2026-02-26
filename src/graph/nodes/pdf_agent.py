import os
from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import AgentState
from src.graph.prompts import PDF_AGENT_PROMPT
from src.graph.llms import get_pdf_llm
from src.utils.pdf import parse_pdf
from src.utils.logger import get_logger

logger = get_logger(__name__)


def pdf_agent_node(state: AgentState):
    """
    PDFAgent: Dedicated subagent that extracts all relevant content from a PDF
    attachment and writes it into state['attachment_context'] for the Researcher.

    Uses Gemini 2.5 Flash Lite (up to 25 000 output tokens) so the entire PDF
    can be processed in a single LLM call — no chunking required.
    """
    logger.info("── PDFAgent ── starting PDF extraction")

    attachment_path = state.get("attachment_path", "")
    messages = state.get("messages", [])

    # Extract the user's latest query for focused extraction
    user_query = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            user_query = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    if not attachment_path or not os.path.exists(attachment_path):
        logger.warning("PDFAgent: file not found at '%s'", attachment_path)
        return {"attachment_context": "PDF file could not be found or read."}

    try:
        with open(attachment_path, "rb") as f:
            file_bytes = f.read()
        full_text = parse_pdf(file_bytes)
    except Exception as e:
        logger.error("PDFAgent: failed to parse PDF: %s", e, exc_info=True)
        return {"attachment_context": f"Failed to parse PDF: {str(e)}"}

    # Cap input to 20 000 characters to stay within context limits
    MAX_CHARS = 20000
    if len(full_text) > MAX_CHARS:
        logger.warning("PDFAgent: text truncated from %d to %d chars", len(full_text), MAX_CHARS)
        full_text = full_text[:MAX_CHARS]

    logger.info("PDFAgent: %d chars ready — calling Gemini 2.5 Flash Lite", len(full_text))

    try:
        llm = get_pdf_llm()
        prompt = ChatPromptTemplate.from_template(PDF_AGENT_PROMPT)
        chain = prompt | llm

        response = chain.invoke({"user_query": user_query, "pdf_content": full_text})
        extracted = response.content.strip()
    except Exception as e:
        logger.error("PDFAgent: LLM extraction failed: %s", e, exc_info=True)
        return {"attachment_context": f"PDF was parsed but LLM extraction failed: {str(e)}"}

    if not extracted:
        extracted = "No relevant content found in the PDF."

    context_block = (
        f"[PDF Attachment Analysis]\n"
        f"The following content was extracted from the attached PDF in relation to the user's query:\n\n"
        f"{extracted}"
    )

    logger.info("PDFAgent: extraction complete → attachment_context set")
    return {"attachment_context": context_block}
