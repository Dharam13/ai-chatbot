"""
News Tool
=========
Fetches top headlines from Newsdata.io API for a given topic / search query.
Returns the top 3 headlines with source and title.

API Docs: https://newsdata.io/documentation
Endpoint: https://newsdata.io/api/1/latest
"""

import httpx
from langchain_core.tools import tool

from app.config import settings


@tool
def get_news_headlines(topic: str) -> str:
    """
    Get the top 3 news headlines for a given topic.
    Use this tool when the user asks for recent news, headlines,
    or current events about any subject.

    Args:
        topic: The news topic or keyword to search for (e.g., "AI", "cricket").

    Returns:
        A formatted string with the top 3 headlines.
    """
    if not settings.news_api_key:
        return "⚠️ News service is not configured (missing API key)."

    try:
        url = "https://newsdata.io/api/1/latest"
        params = {
            "apikey": settings.news_api_key,
            "q": topic,
            "language": "en",
            "size": 3,
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)

        response.raise_for_status()
        data = response.json()

        # Newsdata.io uses "status" field for API-level errors
        if data.get("status") == "error":
            error_msg = data.get("results", {}).get("message", "Unknown API error")
            return f"⚠️ News API error: {error_msg}"

        articles = data.get("results", [])
        if not articles:
            return f"📰 No recent news articles found for '{topic}'."

        lines = [f"📰 Top headlines for \"{topic}\":\n"]
        for idx, article in enumerate(articles, start=1):
            title = article.get("title", "No title")
            source = article.get("source_name", article.get("source_id", "Unknown"))
            link = article.get("link", "")
            lines.append(f"{idx}. [{source}] {title}")
            if link:
                lines.append(f"   🔗 {link}")

        return "\n".join(lines)

    except httpx.TimeoutException:
        return f"⏳ News request for '{topic}' timed out. Please try again."
    except httpx.HTTPStatusError as exc:
        return f"⚠️ News API error (HTTP {exc.response.status_code}). Please try again."
    except Exception as exc:
        return f"⚠️ Could not fetch news for '{topic}'. Error: {exc}"
