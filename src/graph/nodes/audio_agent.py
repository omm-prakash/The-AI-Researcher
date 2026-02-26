import os
from groq import Groq
from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import AgentState
from src.graph.prompts import AUDIO_AGENT_PROMPT
from src.graph.llms import get_llm
from src.utils.logger import get_logger

logger = get_logger(__name__)


def audio_agent_node(state: AgentState):
    """
    AudioAgent: Dedicated subagent that transcribes an audio attachment via
    Groq Whisper and then analyzes the transcript using the logic-reasoning LLM,
    writing its findings to state['attachment_context'] for the Researcher.
    """
    logger.info("── AudioAgent ── starting audio transcription and analysis")

    attachment_path = state.get("attachment_path", "")
    messages = state.get("messages", [])

    # Extract the user's latest query for focused analysis
    user_query = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            user_query = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    if not attachment_path or not os.path.exists(attachment_path):
        logger.warning("AudioAgent: file not found at '%s'", attachment_path)
        return {"attachment_context": "Audio file could not be found or read."}

    # Step 1: Transcribe audio
    try:
        client = Groq()
        filename = os.path.basename(attachment_path)
        logger.info("AudioAgent: transcribing '%s' with Whisper", filename)
        with open(attachment_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(filename, audio_file.read()),
                model="whisper-large-v3",
                response_format="text",
            )
        full_transcript = transcription
        logger.info("AudioAgent: transcription complete — %d chars", len(full_transcript))
    except Exception as e:
        logger.error("AudioAgent: transcription failed: %s", e, exc_info=True)
        return {"attachment_context": f"Audio transcription failed: {str(e)}"}

    # Step 2: Chunk and analyze the transcript
    chunk_size = 4000
    chunks = [full_transcript[i : i + chunk_size] for i in range(0, len(full_transcript), chunk_size)]

    llm = get_llm("logic-reasoning")
    prompt = ChatPromptTemplate.from_template(AUDIO_AGENT_PROMPT)
    chain = prompt | llm

    chunk_results = []
    for i, chunk in enumerate(chunks):
        logger.debug("AudioAgent: analyzing chunk %d/%d", i + 1, len(chunks))
        response = chain.invoke({"user_query": user_query, "audio_content": chunk})
        content = response.content.strip()
        if content.lower() not in ("skipped, not relevant.", "skipped, not relevant"):
            chunk_results.append(f"--- Chunk {i + 1} ---\n{content}")

    extracted = "\n\n".join(chunk_results) if chunk_results else "No relevant content found in the audio."
    context_block = (
        f"[Audio Attachment Analysis]\n"
        f"The following content was extracted from the attached audio file in relation to the user's query:\n\n"
        f"Full Transcript:\n{full_transcript}\n\n"
        f"Focused Analysis:\n{extracted}"
    )

    logger.info("AudioAgent: analysis complete → attachment_context set")
    print('\n\nattachment_context', context_block)
    return {"attachment_context": context_block}
