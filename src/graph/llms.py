models_dict = {
    "agentic-systems": [
        "openai/gpt-oss-20b",               # Context: 128k
        "openai/gpt-oss-120b",              # Context: 128k
        "moonshotai/kimi-k2-instruct-0905", # Context: 256k
        "moonshotai/kimi-k2-instruct"       # Context: 128k
    ],
    "logic-reasoning": [
        "openai/gpt-oss-120b",              # Context: 128k
        "qwen/qwen3-32b",                   # Context: 32k (Native) / 128k (Scaled)
        "llama-3.3-70b-versatile",          # Context: 128k
        "allam-2-7b"                        # Context: 128k
    ],
    "multimodal-moe": [
        "meta-llama/llama-4-maverick-17b-128e-instruct", # Context: 131k
        "meta-llama/llama-4-scout-17b-16e-instruct"      # Context: 131k
    ],
    "efficiency-edge": [
        "openai/gpt-oss-20b",               # Context: 128k
        "llama-3.1-8b-instant",             # Context: 131k
    ],
    "audio-voice": [
        "whisper-large-v3",                 # Context: 30s chunks (Audio)
        "whisper-large-v3-turbo",           # Context: 30s chunks (Audio)
        "canopylabs/orpheus-v1-english",    # Context: 128k
        "canopylabs/orpheus-arabic-saudi"   # Context: 128k
    ],
    "safety-security": [
        "openai/gpt-oss-safeguard-20b",     # Context: 128k
        "meta-llama/llama-prompt-guard-2-86m", # Context: 4k (Classifier)
        "meta-llama/llama-prompt-guard-2-22m", # Context: 4k (Classifier)
        "meta-llama/llama-guard-4-12b",     # Context: 131k
    ]
}

import os
import logging
from groq import RateLimitError, BadRequestError
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.5,
    check_every_n_seconds=0.1,
    max_bucket_size=3,
)

# Errors that should trigger a fallback to the next model instead of aborting.
# - RateLimitError (429): too many requests or quota exceeded
# - BadRequestError: covers context_length_exceeded (max tokens surpassed)
FALLBACK_EXCEPTIONS = (RateLimitError, BadRequestError)


def _make_llm(model_name: str, api_key: str, temperature: float = 0.1) -> ChatGroq:
    """Create a ChatGroq instance with fast-fail settings so fallbacks trigger quickly."""
    return ChatGroq(
        model=model_name,
        api_key=api_key,
        # 0 retries on the same model — fail fast so with_fallbacks() can try the next one
        max_retries=0,
        rate_limiter=rate_limiter,
        temperature=temperature,
    )


def get_llm(category: str, exclude_model: str = None, temperature: float = 0.1):
    """
    Return a ChatGroq LLM (or a chain with automatic fallbacks) for the given category.

    Fallback order = the order of models in models_dict[category].
    A fallback is triggered on RateLimitError (429 / quota) or BadRequestError
    (context-length exceeded), whichever comes first.

    Args:
        category:      Key in models_dict (e.g. "logic-reasoning").
        exclude_model: Optional model name to skip (used by callers that already
                       know one model failed).
    """
    api_key = os.getenv("GROQ_API_KEY")

    available_models = [
        m for m in models_dict.get(category, [])
        if m != exclude_model
    ]

    if not available_models:
        raise ValueError(
            f"No models available for category '{category}' "
            f"(excluded: {exclude_model})"
        )

    primary = _make_llm(available_models[0], api_key, temperature=temperature)
    logger.debug("Primary LLM for '%s': %s", category, available_models[0])

    fallbacks = [_make_llm(name, api_key, temperature=temperature) for name in available_models[1:]]

    if not fallbacks:
        return primary

    # with_fallbacks: on FALLBACK_EXCEPTIONS, transparently retry with the
    # next model in the list. exceptions_to_handle defaults to Exception if
    # omitted, but we narrow it here so only rate-limit / ctx-length errors
    # trigger a switch — other errors (e.g. auth) propagate immediately.
    return primary.with_fallbacks(
        fallbacks,
        exceptions_to_handle=FALLBACK_EXCEPTIONS,
    )


# ---------------------------------------------------------------------------
# PDF / Document understanding LLM
# ---------------------------------------------------------------------------

def get_pdf_llm() -> ChatGoogleGenerativeAI:
    """
    Return a Gemini 2.5 Flash Lite instance tuned for PDF understanding.

    Model  : gemini-2.5-flash-lite
    Tokens : cap at 20 000 max context tokens
    Key    : GOOGLE_API_KEY environment variable
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY is not set. "
            "Please add it to your .env file to use the PDF LLM."
        )

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=api_key,
        max_output_tokens=20000,
        temperature=0.1,
        max_retries=0, # Fail fast so we can trigger the chunk-wise fallback
    )
