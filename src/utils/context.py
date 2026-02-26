from langchain_text_splitters import RecursiveCharacterTextSplitter

def manage_context(text: str, max_tokens: int = 4000) -> str:
    """
    Context Engineering:
    Trims/chunks the gathered facts to fit smartly within an LLM token limit.
    This simple function ensures the injected facts do not overflow the context window.
    """
    # Simple chunker based on characters representing approx tokens
    # Note: A real implementation would use tiktoken or similar
    chunk_size = max_tokens * 4
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=200,
        length_function=len
    )
    docs = text_splitter.split_text(text)
    
    # Return highest priority chunk, or combine a few
    if not docs:
        return text
    return docs[0]

def trim_history(messages, max_chars=20000):
    """
    Trims the message history to prevent TPM limits on Groq.
    Keeps the most recent messages that fit within the character limit.
    """
    trimmed = []
    current_chars = 0
    for msg in reversed(messages):
        msg_len = len(msg.content) if isinstance(msg.content, str) else 500
        if current_chars + msg_len > max_chars:
            break
        trimmed.insert(0, msg)
        current_chars += msg_len
        
    # Ensure we don't start with an orphaned tool message or AIMessage
    if len(trimmed) < len(messages):
        while trimmed and getattr(trimmed[0], 'type', '') != 'human' and trimmed[0].__class__.__name__ != 'HumanMessage':
            trimmed.pop(0)
            
    if not trimmed:
        trimmed = messages[-1:]
        
    return trimmed


def flatten_for_text_llm(messages):
    """
    Text-only Groq models require every message's .content to be a string.
    When a user attaches an image, the HumanMessage.content is a list:
      [{"type":"text","text":"..."}, {"type":"image_url","image_url":{...}}]
    This function returns new message objects with list content replaced by
    a plain string (text parts joined), safe for any text-only LLM.
    """
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    flat = []
    for msg in messages:
        if not isinstance(msg.content, list):
            flat.append(msg)
            continue

        # Extract text parts, skip image/audio parts
        text_parts = [
            part.get("text", "")
            for part in msg.content
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        text = " ".join(text_parts).strip() or "[attachment]"

        # Reconstruct with the same type
        if isinstance(msg, HumanMessage):
            flat.append(HumanMessage(content=text, id=getattr(msg, "id", None)))
        elif isinstance(msg, AIMessage):
            flat.append(AIMessage(content=text, id=getattr(msg, "id", None)))
        elif isinstance(msg, SystemMessage):
            flat.append(SystemMessage(content=text, id=getattr(msg, "id", None)))
        else:
            flat.append(msg)   # unknown type — pass through unchanged
    return flat
