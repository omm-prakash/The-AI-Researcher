models_dict = {
    "agentic-systems": [
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "moonshotai/kimi-k2-instruct-0905",
        "moonshotai/kimi-k2-instruct"
    ],
    "logic-reasoning": [
        "openai/gpt-oss-120b",
        "qwen/qwen3-32b",
        "llama-3.3-70b-versatile",
        "allam-2-7b"
    ],
    "multimodal-moe": [
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "meta-llama/llama-4-scout-17b-16e-instruct"
    ],
    "efficiency-edge": [
        "openai/gpt-oss-20b",
        "llama-3.1-8b-instant",
    ],
    "audio-voice": [
        "whisper-large-v3",
        "whisper-large-v3-turbo",
        "canopylabs/orpheus-v1-english",
        "canopylabs/orpheus-arabic-saudi"
    ],
    "safety-security": [
        "meta-llama/llama-guard-4-12b",
        "meta-llama/llama-prompt-guard-2-22m",
        "meta-llama/llama-prompt-guard-2-86m",
        "openai/gpt-oss-safeguard-20b"
    ]
}



import os
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_groq import ChatGroq

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.5,
    check_every_n_seconds=0.1,
    max_bucket_size=3,
)

def get_llm(category, exclude_model=None):
    api_key = os.getenv("GROQ_API_KEY")
    
    # Get all available models for this category, skipping the excluded one if any
    available_models = [m for m in models_dict.get(category, []) if m != exclude_model]
    
    # If no models found, fallback to a safe small default
    # if not available_models:
    #     available_models = ["llama-3.1-8b-instant"]

    # Instantiate the primary model
    primary_llm = ChatGroq(
        model=available_models[0], 
        api_key=api_key,
        max_retries=1, # reduce retries so it falls back faster
        rate_limiter=rate_limiter
    )
    
    # Create fallbacks for all remaining models in the list
    fallbacks = []
    for model_name in available_models[1:]:
        fallback_llm = ChatGroq(
            model=model_name,
            api_key=api_key,
            max_retries=1,
            rate_limiter=rate_limiter
        )
        fallbacks.append(fallback_llm)
        
    # Bind fallbacks if any exist
    if fallbacks:
        return primary_llm.with_fallbacks(fallbacks)
        
    return primary_llm
