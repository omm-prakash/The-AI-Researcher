import os
from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import AgentState
from src.graph.prompts import PDF_AGENT_PROMPT
from src.graph.llms import get_pdf_llm
from src.utils.pdf import parse_pdf


def pdf_agent_node(state: AgentState):
    """
    PDFAgent: Dedicated subagent that extracts all relevant content from a PDF
    attachment and writes it into state['attachment_context'] for the Researcher.

    Uses Gemini 2.5 Flash Lite (up to 25 000 output tokens) so the entire PDF
    can be processed in a single LLM call — no chunking required.
    """
    print("\n[PDFAgent] Starting PDF extraction...\n")

    attachment_path = state.get("attachment_path", "")
    messages = state.get("messages", [])

    # Extract the user's latest query for focused extraction
    user_query = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            user_query = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    if not attachment_path or not os.path.exists(attachment_path):
        print(f"[PDFAgent] File not found at: {attachment_path}")
        return {"attachment_context": "PDF file could not be found or read."}

    try:
        with open(attachment_path, "rb") as f:
            file_bytes = f.read()
        full_text = parse_pdf(file_bytes)
    except Exception as e:
        print(f"[PDFAgent] Failed to parse PDF: {e}")
        return {"attachment_context": f"Failed to parse PDF: {str(e)}"}

    # Cap input to 20 000 characters to stay within context limits
    MAX_CHARS = 20000
    if len(full_text) > MAX_CHARS:
        print(f"[PDFAgent] PDF text truncated from {len(full_text)} to {MAX_CHARS} characters.")
        full_text = full_text[:MAX_CHARS]

    print(f"[PDFAgent] PDF parsed — {len(full_text)} characters. Calling Gemini 2.5 Flash Lite...")

    try:
        llm = get_pdf_llm()
        prompt = ChatPromptTemplate.from_template(PDF_AGENT_PROMPT)
        chain = prompt | llm

        response = chain.invoke({"user_query": user_query, "pdf_content": full_text})
        extracted = response.content.strip()
    except Exception as e:
        print(f"[PDFAgent] LLM call failed: {e}")
        return {"attachment_context": f"PDF was parsed but LLM extraction failed: {str(e)}"}

    if not extracted:
        extracted = "No relevant content found in the PDF."

    context_block = (
        f"[PDF Attachment Analysis]\n"
        f"The following content was extracted from the attached PDF in relation to the user's query:\n\n"
        f"{extracted}"
    )

    print("[PDFAgent] Extraction complete.\n")
    return {"attachment_context": context_block}
