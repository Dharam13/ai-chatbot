"""
Wikipedia Tool
==============
Fetches a short summary from Wikipedia for a given search query.
Uses the ``wikipedia`` Python package for reliable extraction.
"""

import wikipedia
from langchain_core.tools import tool


@tool
def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia and return a short summary of the topic.
    Use this tool when the user asks about a person, place, concept,
    historical event, or any general-knowledge topic that Wikipedia
    would cover well.

    Args:
        query: The topic to search for on Wikipedia (e.g., "Python programming").

    Returns:
        A 3-4 sentence summary from the most relevant Wikipedia article.
    """
    try:
        # Attempt to get a summary directly
        summary = wikipedia.summary(query, sentences=3, auto_suggest=True)
        page = wikipedia.page(query, auto_suggest=True)
        return (
            f"📖 **{page.title}**\n\n"
            f"{summary}\n\n"
            f"🔗 Read more: {page.url}"
        )

    except wikipedia.exceptions.DisambiguationError as exc:
        # Multiple matches — pick the first suggestion
        options = exc.options[:5]
        try:
            summary = wikipedia.summary(options[0], sentences=3)
            return (
                f"📖 **{options[0]}**\n\n{summary}\n\n"
                f"ℹ️ Other possible topics: {', '.join(options[1:])}"
            )
        except Exception:
            return (
                f"🔍 Multiple Wikipedia articles match '{query}'. "
                f"Try being more specific. Suggestions: {', '.join(options)}"
            )

    except wikipedia.exceptions.PageError:
        return f"❌ No Wikipedia article found for '{query}'. Try a different search term."

    except Exception as exc:
        return f"⚠️ Wikipedia lookup failed for '{query}'. Error: {exc}"
