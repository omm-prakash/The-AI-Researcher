import pytest
from src.main import app
from src.utils.context import manage_context

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_context_manager():
    """Test the context engineering text chunking function"""
    long_text = "A" * 10000
    chunked = manage_context(long_text, max_tokens=100)
    # 100 tokens * 4 chars = 400 chars chunk size limit
    assert len(chunked) <= 400

# def test_chat_endpoint_no_db(client):
#     response = client.post("/chat", json={"thread_id": "test_1", "message": "Hi"})
#     assert response.status_code in [200, 500]
