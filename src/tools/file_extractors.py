import os
import base64
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from groq import Groq

from src.graph.prompts import PDF_AGENT_PROMPT, IMAGE_AGENT_PROMPT, AUDIO_AGENT_PROMPT
from src.graph.llms import get_pdf_llm, get_llm
from src.utils.pdf import parse_pdf
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Tool Schemas ──────────────────────────────────────────────────────────────

class PDFExtractInput(BaseModel):
    attachment_path: str = Field(description="The absolute path to the PDF file to extract.")
    user_query: str = Field(description="The user's query to focus the extraction on.")

class ImageExtractInput(BaseModel):
    attachment_path: str = Field(description="The absolute path to the image file to analyze.")
    user_query: str = Field(description="The user's query to focus the analysis on.")

class AudioExtractInput(BaseModel):
    attachment_path: str = Field(description="The absolute path to the audio file to transcribe and analyze.")
    user_query: str = Field(description="The user's query to focus the analysis on.")


# ── PDF Tool ──────────────────────────────────────────────────────────────────

@tool("pdf_extractor_tool", args_schema=PDFExtractInput)
def pdf_extractor_tool(attachment_path: str, user_query: str) -> str:
    """
    Extracts relevant content from a PDF document based on the user's query.
    Use this tool whenever the user has attached a PDF file.
    """
    logger.info("── pdf_extractor_tool ── starting PDF extraction")

    if not attachment_path or not os.path.exists(attachment_path):
        return "PDF file could not be found or read."

    try:
        with open(attachment_path, "rb") as f:
            file_bytes = f.read()
        full_text = parse_pdf(file_bytes)
    except Exception as e:
        return f"Failed to parse PDF: {str(e)}"

    extracted = None
    primary_err = None

    # Try Primary Approach: Gemini 2.5 Flash Lite
    try:
        MAX_CHARS = 20000
        primary_text = full_text
        if len(primary_text) > MAX_CHARS:
            primary_text = primary_text[:MAX_CHARS]
        
        llm = get_pdf_llm()
        prompt = ChatPromptTemplate.from_template(PDF_AGENT_PROMPT)
        chain = prompt | llm

        response = chain.invoke({"user_query": user_query, "pdf_content": primary_text})
        extracted = response.content.strip()
    except Exception as e:
        primary_err = str(e)
        logger.warning("pdf_extractor_tool (Primary) failed: %s", e)

    # Try Fallback Approach: Chunk-wise understanding
    if extracted is None:
        try:
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
                last_summary = results[-1] if results else ""
                response = fallback_chain.invoke({"task": user_query, "chunk": chunk + last_summary})
                results.append(f"--- Chunk {index + 1} Analysis ---\n{response.content}")

            extracted = "\n".join(results)
        except Exception as fallback_err:
            return f"PDF was parsed but extraction failed. Primary err: {primary_err}. Fallback err: {fallback_err}."

    if not extracted:
        extracted = "No relevant content found in the PDF."

    return (
        f"[PDF Attachment Analysis]\n"
        f"The following content was extracted from the attached PDF in relation to the query:\n\n"
        f"{extracted}"
    )


# ── Image Tool ────────────────────────────────────────────────────────────────

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

@tool("image_extractor_tool", args_schema=ImageExtractInput)
def image_extractor_tool(attachment_path: str, user_query: str) -> str:
    """
    Analyzes an image file to answer visual questions or extract textual/visual data.
    Use this tool whenever the user has attached an image file.
    """
    logger.info("── image_extractor_tool ── starting image analysis")

    if not attachment_path or not os.path.exists(attachment_path):
        return "Image file could not be found or read."

    try:
        with open(attachment_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        return f"Failed to read image file: {str(e)}"

    ext = attachment_path.lower().rsplit(".", 1)[-1]
    mime_type = MIME_MAP.get(ext, "image/jpeg")
    system_text = IMAGE_AGENT_PROMPT.format(user_query=user_query)

    api_key = os.getenv("GROQ_API_KEY")
    extracted = None
    last_error = None

    for model in VISION_MODELS:
        try:
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
            break
        except Exception as e:
            last_error = e
            continue

    if extracted is None:
        error_msg = str(last_error) if last_error else "All vision models failed"
        return f"Image analysis failed: {error_msg}"
    print(extracted)
    return (
        "[Image Attachment Analysis]\n"
        "The following analysis was performed on the attached image "
        "in relation to the query:\n\n"
        f"{extracted}"
    )


# ── Audio Tool ────────────────────────────────────────────────────────────────

@tool("audio_extractor_tool", args_schema=AudioExtractInput)
def audio_extractor_tool(attachment_path: str, user_query: str) -> str:
    """
    Transcribes and analyzes an audio file based on the user's query.
    Use this tool whenever the user has attached an audio file.
    """
    logger.info("── audio_extractor_tool ── starting audio analysis")

    if not attachment_path or not os.path.exists(attachment_path):
        return "Audio file could not be found or read."

    # Step 1: Transcribe audio
    try:
        client = Groq()
        filename = os.path.basename(attachment_path)
        with open(attachment_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(filename, audio_file.read()),
                model="whisper-large-v3",
                response_format="text",
            )
        full_transcript = transcription
    except Exception as e:
        return f"Audio transcription failed: {str(e)}"

    # Step 2: Chunk and analyze the transcript
    chunk_size = 4000
    chunks = [full_transcript[i : i + chunk_size] for i in range(0, len(full_transcript), chunk_size)]

    llm = get_llm("logic-reasoning")
    prompt = ChatPromptTemplate.from_template(AUDIO_AGENT_PROMPT)
    chain = prompt | llm

    chunk_results = []
    for i, chunk in enumerate(chunks):
        response = chain.invoke({"user_query": user_query, "audio_content": chunk})
        content = response.content.strip()
        if content.lower() not in ("skipped, not relevant.", "skipped, not relevant"):
            chunk_results.append(f"--- Chunk {i + 1} ---\n{content}")

    extracted = "\n\n".join(chunk_results) if chunk_results else "No relevant content found in the audio."
    return (
        f"[Audio Attachment Analysis]\n"
        f"The following content was extracted from the attached audio file:\n\n"
        f"Full Transcript:\n{full_transcript}\n\n"
        f"Focused Analysis:\n{extracted}"
    )
