from langchain_core.tools import tool
from src.graph.llms import get_llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os
from groq import Groq

class ReadAudioInput(BaseModel):
    file_path: str = Field(description="The absolute path to the audio file.")
    task: str = Field(description="The task or question to apply to the audio content.")

@tool("read_audio_tool", args_schema=ReadAudioInput)
def read_audio_tool(file_path: str, task: str) -> str:
    """Analyze an audio file by transcribing it and extracting/summarizing data based on a specific task."""
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
        
    try:
        # Transcribe audio using native Groq client
        client = Groq()
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path.split("/")[-1], file.read()),
                model="whisper-large-v3",
                response_format="text"
            )
            
        full_text = transcription
        
        # Chunk text into ~4000 char pieces to avoid blowing up the context or rate limits
        chunk_size = 4000
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        
        llm = get_llm("logic-reasoning")
        prompt = ChatPromptTemplate.from_template(
            "You are an AI assistant helping a researcher. Based on the following transcribed audio chunk, "
            "perform the following task:\nTask: {task}\n\nAudio Transcription Chunk:\n{chunk}\n\n"
            "If the chunk does not contain relevant information, just briefly return 'Skipped, not relevant.':"
        )
        chain = prompt | llm
        
        results = []
        for index, chunk in enumerate(chunks):
            response = chain.invoke({"task": task, "chunk": chunk})
            results.append(f"--- Chunk {index + 1} Analysis ---\n{response.content}")
            
        return "\n".join(results)
    except Exception as e:
        return f"Failed to analyze audio: {str(e)}"
