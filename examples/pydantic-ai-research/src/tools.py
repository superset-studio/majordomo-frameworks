"""Tool definitions for the research agent.

This module defines tools that agents can use during execution.
Tools are logged through the gateway as part of the agent's workflow.
"""

import os
from dataclasses import dataclass

from tavily import TavilyClient


@dataclass
class SearchResult:
    """A single search result from web search."""

    title: str
    url: str
    content: str
    score: float


def web_search(query: str, max_results: int = 5) -> list[SearchResult]:
    """Search the web using Tavily API.

    Args:
        query: The search query
        max_results: Maximum number of results to return

    Returns:
        List of search results with title, URL, and content snippet
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        # Return mock results if no API key (for testing)
        return [
            SearchResult(
                title=f"Mock result for: {query}",
                url="https://example.com/mock",
                content=f"This is a mock search result for '{query}'. "
                "Set TAVILY_API_KEY for real search results.",
                score=0.9,
            )
        ]

    client = TavilyClient(api_key=api_key)
    response = client.search(query=query, max_results=max_results)

    return [
        SearchResult(
            title=result.get("title", "Untitled"),
            url=result.get("url", ""),
            content=result.get("content", ""),
            score=result.get("score", 0.0),
        )
        for result in response.get("results", [])
    ]
