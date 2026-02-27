import os
import uvicorn

if __name__ == "__main__":
    # Highly optimized Uvicorn settings for 1 vCPU, 1GB RAM instances (e.g. OCI VM.Standard.E2.1.Micro)
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=1, # 1 physical core = 1 worker to prevent CPU thrashing
        log_level="warning",  # Minimize disk I/O from extensive logging
        access_log=False,
        proxy_headers=True,
        forwarded_allow_ips=os.getenv("TRUSTED_PROXIES", "127.0.0.1"),
        limit_max_requests=800,  # Recycle worker every 800 requests to release RAM back to OS
        limit_max_requests_jitter=100,  # Wait a random bit before recycling so we don't drop connections instantly
        timeout_keep_alive=65,  # 65s TCP keep-alive to support long-running LLM completions without dropping
        timeout_graceful_shutdown=30
    )
