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
