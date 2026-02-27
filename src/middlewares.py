import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log each request with its method, path, and processing time."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logger.info("")
        logger.info(f"Received request: {request.method} {request.url.path}")

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(f"Completed request in {process_time:.2f}s with status {response.status_code}")
        response.headers["X-Process-Time"] = str(process_time)

        return response
