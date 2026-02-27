import os
from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import AgentState
from src.graph.prompts import PDF_AGENT_PROMPT
from src.graph.llms import get_pdf_llm, get_llm
from src.utils.pdf import parse_pdf
from src.utils.logger import get_logger

logger = get_logger(__name__)


def pdf_agent_node(state: AgentState):
    """
    PDFAgent: Dedicated subagent that extracts all relevant content from a PDF
    attachment and writes it into state['attachment_context'] for the Researcher.

    Primary attempt: Uses Gemini 2.5 Flash Lite with a max context of 20K chars.
    Fallback: If primary fails (e.g. rate limit), uses chunk-wise processing.
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

    extracted = None
    primary_err = None

    # Try Primary Approach: Gemini 2.5 Flash Lite
    try:
        # Cap input to 20 000 characters to stay within context limits
        MAX_CHARS = 20000
        primary_text = full_text
        if len(primary_text) > MAX_CHARS:
            logger.warning("PDFAgent (Primary): text truncated from %d to %d chars", len(primary_text), MAX_CHARS)
            primary_text = primary_text[:MAX_CHARS]

        logger.info("PDFAgent (Primary): calling Gemini 2.5 Flash Lite with %d chars", len(primary_text))
        
        llm = get_pdf_llm()
        prompt = ChatPromptTemplate.from_template(PDF_AGENT_PROMPT)
        chain = prompt | llm

        response = chain.invoke({"user_query": user_query, "pdf_content": primary_text})
        extracted = response.content.strip()
        logger.info("PDFAgent (Primary): extraction successful")
    except Exception as e:
        primary_err = str(e)
        logger.warning("PDFAgent (Primary) failed: %s. Falling back to chunk-wise processing...", e)

    # Try Fallback Approach: Chunk-wise understanding
    if extracted is None:
        try:
            logger.info("PDFAgent (Fallback): starting chunk-wise processing of %d total chars", len(full_text))
            chunk_size = 4000
            chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
            
            fallback_llm = get_llm("logic-reasoning")
            fallback_prompt = ChatPromptTemplate.from_template(
                "You are an AI assistant helping a researcher. Based on the following PDF text chunk, "
                "perform the following task:\nTask: {task}\n\nPDF Chunk:\n{chunk}\n\n"
                "You are given current chunk and previous chunk summary, use it to generate a new summary. "
                "Summarize the chunk in 700 words. "
                "If the chunk does not contain relevant information, just briefly return 'Skipped, not relevant.':"
            )
            fallback_chain = fallback_prompt | fallback_llm
            
            results = []
            for index, chunk in enumerate(chunks):
                logger.debug("PDFAgent (Fallback): processing chunk %d/%d", index + 1, len(chunks))
                last_summary = results[-1] if results else ""
                response = fallback_chain.invoke({"task": user_query, "chunk": chunk + last_summary})
                results.append(f"--- Chunk {index + 1} Analysis ---\n{response.content}")

            extracted = "\n".join(results)
            logger.info("PDFAgent (Fallback): extraction successful (%d chunks)", len(chunks))
        except Exception as fallback_err:
            logger.error("PDFAgent (Fallback) failed: %s", fallback_err, exc_info=True)
            return {"attachment_context": f"PDF was parsed but both extraction methods failed. Primary err: {primary_err}. Fallback err: {fallback_err}."}

    if not extracted:
        extracted = "No relevant content found in the PDF."

    context_block = (
        f"[PDF Attachment Analysis]\n"
        f"The following content was extracted from the attached PDF in relation to the user's query:\n\n"
        f"{extracted}"
    )

    logger.info("PDFAgent: extraction complete → attachment_context set")
    # print('\\n\\n pdf context', context_block)
    return {"attachment_context": context_block}
