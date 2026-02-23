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
