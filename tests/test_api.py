import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.main import app
from src.utils.context import manage_context
from src.graph.builder import build_graph

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

def test_graph_compilation():
    """Test if the LangGraph correctly compiles with the Casual node"""
    builder = build_graph()
    # Check if compilation passes without errors
    agent = builder.compile()
    assert agent is not None
