import os
from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import AgentState
from src.graph.prompts import PDF_AGENT_PROMPT
from src.graph.llms import get_llm
from src.utils.pdf import parse_pdf


def pdf_agent_node(state: AgentState):
    """
    PDFAgent: Dedicated subagent that extracts all relevant content from a PDF
    attachment and writes it into state['attachment_context'] for the Researcher.
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

    # Chunk the PDF text to avoid context-window overflow
    chunk_size = 4000
    chunks = [full_text[i : i + chunk_size] for i in range(0, len(full_text), chunk_size)]

    llm = get_llm("logic-reasoning")
    prompt = ChatPromptTemplate.from_template(PDF_AGENT_PROMPT)
    chain = prompt | llm

    chunk_results = []
    for i, chunk in enumerate(chunks):
        print(f"[PDFAgent] Processing chunk {i + 1}/{len(chunks)}")
        response = chain.invoke({"user_query": user_query, "pdf_content": chunk})
        content = response.content.strip()
        if content.lower() not in ("skipped, not relevant.", "skipped, not relevant"):
            chunk_results.append(f"--- Chunk {i + 1} ---\n{content}")

    extracted = "\n\n".join(chunk_results) if chunk_results else "No relevant content found in the PDF."
    context_block = (
        f"[PDF Attachment Analysis]\n"
        f"The following content was extracted from the attached PDF in relation to the user's query:\n\n"
        f"{extracted}"
    )

    print("[PDFAgent] Extraction complete.\n")
    return {"attachment_context": context_block}
