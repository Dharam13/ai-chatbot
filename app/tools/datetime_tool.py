"""
DateTime Tool
=============
Returns the current date, time, and day of the week.
No external API required — uses Python's built-in ``datetime`` module.
"""

from datetime import datetime

from langchain_core.tools import tool


@tool
def get_current_datetime() -> str:
    """
    Get the current date, time, and day of the week.
    Use this tool when the user asks what day it is, the current time,
    today's date, or anything related to the present date/time.

    Returns:
        A formatted string with the current date, time, and day.
    """
    try:
        now = datetime.now()
        return (
            f"📅 Date: {now.strftime('%B %d, %Y')}\n"
            f"🕐 Time: {now.strftime('%I:%M %p')}\n"
            f"📆 Day: {now.strftime('%A')}"
        )
    except Exception as exc:
        return f"Sorry, I couldn't retrieve the current date/time. Error: {exc}"
