from fastapi.testclient import TestClient
from src.main import app
from src.utils.context import manage_context

client = TestClient(app)

def test_context_manager():
    """Test the context engineering text chunking function"""
    long_text = "A" * 10000
    chunked = manage_context(long_text, max_tokens=100)
    # 100 tokens * 4 chars = 400 chars chunk size limit
    assert len(chunked) <= 400

# To run the API integration test, the Postgres DB must be running.
# Example payload for manual testing or when DB is up:
# def test_chat_endpoint_no_db():
#     response = client.post("/chat", json={"thread_id": "test_1", "message": "Hi"})
#     assert response.status_code in [200, 500]  # 500 if DB is down
