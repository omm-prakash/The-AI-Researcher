"""
Search tools for the Researcher agent.

Primary  : Tavily Search   — fast, accurate AI-optimized search
           Tavily Extract  — fetch and extract full page content from URLs
Fallback : DuckDuckGo      — used automatically when Tavily raises any exception
"""

import os
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langchain_community.tools import DuckDuckGoSearchRun
from pydantic import BaseModel, Field
from src.utils.context import manage_context
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Tavily clients (lazy, so we don't fail at import if key is missing) ───────

def _tavily_search_client():
    return TavilySearch(
        max_results=5,
        topic="general",
    )


# ── Tool schemas ──────────────────────────────────────────────────────────────

class SearchInput(BaseModel):
    query: str = Field(description="The search query to look up on the internet.")

class ExtractInput(BaseModel):
    urls: list[str] = Field(description="List of URLs to fetch and extract full content from.")


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool("tavily_search", args_schema=SearchInput)
def tavily_search_tool(query: str) -> str:
    """
    Search the internet using Tavily for accurate, up-to-date information.
    Returns a structured list of search results with titles, URLs, and snippets.
    Use this as your PRIMARY search tool.
    Falls back to DuckDuckGo automatically if Tavily is unavailable.
    """
    try:
        client = _tavily_search_client()
        results = client.invoke(query)
        if not results:
            return "No results found."
        # Format results into a readable block
        lines = []
        for r in results:
            lines.append(f"Title: {r.get('title', 'N/A')}")
            lines.append(f"URL:   {r.get('url', 'N/A')}")
            lines.append(f"Snippet: {r.get('content', '')[:400]}")
            lines.append("")
        raw = "\n".join(lines)
        logger.info("tavily_search: %d results for '%s'", len(results), query[:60])
        return manage_context(raw, max_tokens=1200)
    except Exception as e:
        logger.warning("tavily_search failed (%s) — falling back to DuckDuckGo", e)
        try:
            ddg = DuckDuckGoSearchRun()
            raw = ddg.run(query)
            logger.info("DuckDuckGo fallback succeeded for '%s'", query[:60])
            return manage_context(raw, max_tokens=800)
        except Exception as e2:
            logger.error("DuckDuckGo fallback also failed: %s", e2)
            return (
                f"Both Tavily and DuckDuckGo search failed. "
                f"Tavily error: {e}. DuckDuckGo error: {e2}. "
                "Summarize based on your training knowledge."
            )


@tool("tavily_extract", args_schema=ExtractInput)
def tavily_extract_tool(urls: list[str]) -> str:
    """
    Fetch and extract the full text content of one or more web pages using Tavily.
    Use this AFTER tavily_search when you need the complete content of a specific URL.
    Only pass URLs that are highly relevant — do not extract more than 3 pages at once.
    Falls back gracefully if extraction fails.
    """
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = client.extract(urls=urls[:3])   # cap at 3 pages
        results = response.get("results", [])
        if not results:
            return "No content could be extracted from the provided URLs."
        lines = []
        for r in results:
            lines.append(f"URL: {r.get('url', 'N/A')}")
            lines.append(r.get("raw_content", "")[:2000])
            lines.append("")
        raw = "\n".join(lines)
        logger.info("tavily_extract: extracted %d page(s)", len(results))
        return manage_context(raw, max_tokens=2000)
    except Exception as e:
        logger.warning("tavily_extract failed: %s", e)
        return f"Page extraction failed: {e}. Use tavily_search results instead."
