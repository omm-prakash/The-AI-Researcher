from langchain_core.tools import tool
from src.graph.llms import get_llm
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
import base64
import os

class ReadImageInput(BaseModel):
    file_path: str = Field(description="The absolute path to the image file.")
    task: str = Field(description="The task or question to apply to the image content.")

@tool("read_image_tool", args_schema=ReadImageInput)
def read_image_tool(file_path: str, task: str) -> str:
    """Analyze an image file and extract/summarize information based on a specific task."""
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
        
    try:
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        llm = get_llm("multimodal-moe")
        
        # Determine mime type
        ext = file_path.lower().split('.')[-1]
        mime_type = "image/jpeg"
        if ext == "png": mime_type = "image/png"
        elif ext == "webp": mime_type = "image/webp"
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": f"Task: {task}"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{encoded_string}",
                    },
                },
            ]
        )
        
        response = llm.invoke([message])
        return response.content
    except Exception as e:
        return f"Failed to analyze image: {str(e)}"
