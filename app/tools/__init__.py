"""
Tools Subpackage
================
LangChain-compatible tools that the agent can invoke.
Each tool is decorated with ``@tool`` and has a clear docstring
so the LLM knows *when* and *how* to use it.

All tools are re-exported here for convenient import.
"""

from app.tools.datetime_tool import get_current_datetime
from app.tools.weather_tool import get_weather
from app.tools.news_tool import get_news_headlines
from app.tools.calculator_tool import calculate
from app.tools.wikipedia_tool import search_wikipedia

# Ordered list passed to the agent executor.
ALL_TOOLS = [
    get_current_datetime,
    get_weather,
    get_news_headlines,
    calculate,
    search_wikipedia,
]

__all__ = [
    "ALL_TOOLS",
    "get_current_datetime",
    "get_weather",
    "get_news_headlines",
    "calculate",
    "search_wikipedia",
]
