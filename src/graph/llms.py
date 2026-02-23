models_dict = {
    "agentic-systems": [
        "groq/compound", 
        "groq/compound-mini"
    ],
    "logic-reasoning": [
        "gpt-oss-120b", 
        "qwen3-32b", 
        "llama-3.3-70b"
    ],
    "multimodal-moe": [
        "llama-4-maverick", 
        "llama-4-scout"
    ],
    "efficiency-edge": [
        "llama-3.1-8b-instant"
        "gpt-oss-20b", 
    ],
    "audio-voice": [
        "whisper-large-v3", 
        "orpheus-v1-english"
    ],
    "safety-security": [
        "llama-guard-4-12b", 
        "llama-prompt-guard"
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
    if exclude_model is None:
        model_name = models_dict[category][0]
    else:
        for name in models_dict[category]:
            if name != exclude_model:
                model_name = name
                break

    return ChatGroq(
        model=model_name, 
        api_key=api_key,
        max_retries=2,
        rate_limiter=rate_limiter
    )
