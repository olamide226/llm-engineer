import os
from functools import lru_cache

from dotenv import load_dotenv
from tavily import TavilyClient

# Load environment variables from .env file
load_dotenv()


@lru_cache(maxsize=1)
def setup_tavily_client() -> TavilyClient:
    """Return the initialized Tavily client"""
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables")
    return TavilyClient(api_key=tavily_api_key)


tavily = setup_tavily_client()


def tavily_search(query):
    """Perform a web search using the Tavily API to get up-to-date information or additional context."""
    try:
        response = tavily.qna_search(query=query, search_depth="advanced")
        return response
    except Exception as exc:
        return f"Error performing search: {str(exc)}"
