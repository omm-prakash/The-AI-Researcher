from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from pydantic import BaseModel, Field
from src.utils.context import manage_context

class SearchInput(BaseModel):
    query: str = Field(description="The search query to look up on the internet.")

@tool("internet_search_tool", args_schema=SearchInput)
def internet_search_tool(query: str) -> str:
    """Search the internet for accurate, up-to-date facts about a given query."""
    search = DuckDuckGoSearchRun()
    try:
        raw_result = search.run(query)
        # Prevent 413 Payload Too Large by strictly chunking the result
        return manage_context(raw_result, max_tokens=500)
    except Exception as e:
        return f"Search failed due to rate limits or network error: {str(e)}. Please summarize based on what you already know or try a drastically different query."
