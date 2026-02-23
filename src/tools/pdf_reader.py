from langchain_core.tools import tool
import os

@tool
def read_pdf_tool(file_path: str) -> str:
    """Reads and extracts text from a PDF file given its absolute file_path."""
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
        
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            return parse_pdf(file_bytes)
    except Exception as e:
        return f"Failed to read PDF: {str(e)}"
