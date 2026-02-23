import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenticMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Logging and latency tracking
        start_time = time.time()
        logger.info(f"Received request: {request.method} {request.url}")
        
        # 2. Moderation placeholder (e.g. Reject bad words)
        # body = await request.body()
        # if b"toxic_word" in body:
        #     return JSONResponse(status_code=400, content={"error": "Inappropriate content"})
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"Completed request in {process_time:.2f}s with status {response.status_code}")
        
        # 3. Token tracking could also be injected here via Langchain callbacks
        # For simplicity, we just inject standard HTTP headers
        response.headers["X-Process-Time"] = str(process_time)
        return response
