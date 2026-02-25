from langchain_core.tools import tool
from src.utils.pdf import parse_pdf
from src.graph.llms import get_llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os

class ReadPDFInput(BaseModel):
    file_path: str = Field(description="The absolute path to the PDF file.")
    task: str = Field(description="The task or question to apply to the PDF content.")

@tool("read_pdf_tool", args_schema=ReadPDFInput)
def read_pdf_tool(file_path: str, task: str) -> str:
    """Read a PDF file and extract/summarize information from it based on a specific task. Handles large PDFs chunk-by-chunk."""
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
        
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            full_text = parse_pdf(file_bytes)
            
        # Chunk text to avoid prompt size limits
        chunk_size = 4000
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        
        llm = get_llm("logic-reasoning")
        prompt = ChatPromptTemplate.from_template(
            "You are an AI assistant helping a researcher. Based on the following PDF text chunk, "
            "perform the following task:\nTask: {task}\n\nPDF Chunk:\n{chunk}\n\n"
            "Summarize the chunk in 200 words."
            "If the chunk does not contain relevant information, just briefly return 'Skipped, not relevant.':"
        )
        chain = prompt | llm
        
        results = []
        for index, chunk in enumerate(chunks):
            response = chain.invoke({"task": task, "chunk": chunk})
            results.append(f"--- Chunk {index + 1} Analysis ---\n{response.content}")
            
        return "\n".join(results)
    except Exception as e:
        return f"Failed to read PDF: {str(e)}"
