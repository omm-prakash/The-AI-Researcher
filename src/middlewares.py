import time
import logging
from flask import request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_middlewares(app):
    @app.before_request
    def before_request():
        request.start_time = time.time()
        logger.info('')
        logger.info(f"Received request: {request.method} {request.path}")

    @app.after_request
    def after_request(response):
        if hasattr(request, 'start_time'):
            process_time = time.time() - request.start_time
            logger.info(f"Completed request in {process_time:.2f}s with status {response.status_code}")
            response.headers["X-Process-Time"] = str(process_time)
        return response
