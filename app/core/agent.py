"""
Chat response runner.

This module keeps the chatbot path simple:
1. Pick the available LLM.
2. Send the system prompt, chat history, and user message.
3. Save the conversation in memory.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

import httpx
from loguru import logger

from app.config import settings
from app.core.llm import LLMProviderName, get_llm_with_fallback, _build_groq
from app.core.memory import memory_manager
from app.exceptions import LLMUnavailableError
from app.prompts.system import build_chat_prompt


@dataclass
class ChatResult:
    """Response returned by the chat runner."""

    reply: str
    llm_provider: LLMProviderName
    tools_used: List[str] = field(default_factory=list)


def _message_text(response: object) -> str:
    """Extract plain text from a LangChain chat model response."""
    content = getattr(response, "content", response)

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts).strip()

    return str(content).strip()


def _current_datetime_reply(user_message: str) -> str | None:
    """Return a direct date/time answer when the user asks for it."""
    text = user_message.lower()
    if any(word in text for word in ["weather", "temperature", "temp"]):
        return None

    asks_time = any(word in text for word in ["time", "clock"])
    asks_date = any(word in text for word in ["date", "day", "today"])

    if not asks_time and not asks_date:
        return None

    now = datetime.now()

    if asks_time and not asks_date:
        return f"The current time is {now.strftime('%I:%M %p')}."

    if asks_date and not asks_time:
        return f"Today is {now.strftime('%A, %B %d, %Y')}."

    return f"Today is {now.strftime('%A, %B %d, %Y')} and the time is {now.strftime('%I:%M %p')}."


def _weather_city(user_message: str) -> str | None:
    """Extract a simple city name from common weather questions."""
    text = user_message.strip()
    match = re.search(
        r"\b(?:weather|temperature|temp)\s+(?:in|at|for|of)\s+([a-zA-Z .'-]+)",
        text,
        re.IGNORECASE,
    )
    if match:
        return _clean_city_name(match.group(1))

    match = re.search(
        r"\b(?:in|at|for)\s+([a-zA-Z .'-]+)\s+(?:weather|temperature|temp)\b",
        text,
        re.IGNORECASE,
    )
    if match:
        return _clean_city_name(match.group(1))

    return None


def _clean_city_name(city: str) -> str:
    """Remove common trailing words that are not part of the city name."""
    city = city.strip(" .?")
    city = re.sub(
        r"\s+(right now|now|today|currently|please)$",
        "",
        city,
        flags=re.IGNORECASE,
    )
    return city.strip(" .?")


async def _weather_reply(user_message: str) -> str | None:
    """Return live weather for simple weather questions."""
    text = user_message.lower()
    if not any(word in text for word in ["weather", "temperature", "temp"]):
        return None

    city = _weather_city(user_message)
    if city and city.lower() in {"my location", "current location", "here"}:
        city = None

    if not city:
        return "Which city should I check the weather for?"

    if not settings.openweather_api_key:
        return "Weather is not configured yet. Please add OPENWEATHER_API_KEY in .env."

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": settings.openweather_api_key,
        "units": "metric",
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, params=params)

        if response.status_code == 404:
            return f"I couldn't find weather for '{city}'. Please check the city name."

        response.raise_for_status()
        data = response.json()
    except httpx.TimeoutException:
        return f"The weather request for {city} timed out. Please try again."
    except Exception:
        logger.exception(f"Weather lookup failed for city={city}")
        return f"I couldn't fetch the weather for {city} right now."

    temp = round(data["main"]["temp"])
    feels_like = round(data["main"]["feels_like"])
    condition = data["weather"][0]["description"]
    humidity = data["main"]["humidity"]
    city_name = data.get("name", city)

    return (
        f"The weather in {city_name} is {temp} C with {condition}. "
        f"It feels like {feels_like} C, with {humidity}% humidity."
    )


async def _quick_reply(user_message: str) -> tuple[str, str] | None:
    """Answer real-time queries without using the LLM."""
    datetime_reply = _current_datetime_reply(user_message)
    if datetime_reply:
        return datetime_reply, "datetime"

    weather_reply = await _weather_reply(user_message)
    if weather_reply:
        return weather_reply, "weather"

    text = user_message.lower()
    if "location" in text or "where am i" in text:
        return "I cannot access your exact location. Tell me your city and I can help with local time or weather.", "location"

    return None


async def run_chat(session_id: str, user_message: str) -> ChatResult:
    """Generate a chat response for one user message."""
    quick_reply = await _quick_reply(user_message)
    if quick_reply:
        reply, tool_name = quick_reply
        memory_manager.add_user_message(session_id, user_message)
        memory_manager.add_ai_message(session_id, reply)
        return ChatResult(
            reply=reply,
            llm_provider="ollama",
            tools_used=[tool_name],
        )

    llm, provider = await get_llm_with_fallback()
    chat_history = memory_manager.get_messages(session_id)
    prompt = build_chat_prompt()
    messages = prompt.format_messages(
        input=user_message,
        chat_history=chat_history,
    )

    logger.info(f"Processing message for session={session_id} via {provider}")

    try:
        response = await llm.ainvoke(messages)
    except Exception as llm_err:
        if provider == "ollama" and settings.enable_groq_fallback:
            logger.warning(f"Ollama failed at runtime: {llm_err}. Falling back to Groq.")
            try:
                llm = _build_groq()
                response = await llm.ainvoke(messages)
                provider = "groq"
            except Exception as groq_err:
                logger.error(f"Groq fallback also failed: {groq_err}")
                raise LLMUnavailableError(
                    "Both Ollama and Groq failed. Check Ollama first, then check your Groq API key/quota."
                )
        else:
            logger.error(f"{provider} failed at runtime: {llm_err}")
            raise LLMUnavailableError(
                "The selected LLM failed to respond. Check that Ollama is running "
                f"and that '{settings.ollama_model}' is installed."
            )

    reply = _message_text(response) or "I'm sorry, I couldn't generate a response."

    memory_manager.add_user_message(session_id, user_message)
    memory_manager.add_ai_message(session_id, reply)

    logger.info(f"Response generated | session={session_id} | provider={provider}")

    return ChatResult(
        reply=reply,
        llm_provider=provider,
        tools_used=[],
    )
