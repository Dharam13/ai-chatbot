"""
Weather Tool
============
Fetches live weather data from the OpenWeatherMap API.
Returns temperature, condition, and humidity for a given city.
"""

import httpx
from langchain_core.tools import tool

from app.config import settings


@tool
def get_weather(city: str) -> str:
    """
    Get the current weather for a given city.
    Use this tool when the user asks about the weather, temperature,
    or atmospheric conditions in any city or location.

    Args:
        city: Name of the city to look up (e.g., "London", "New York").

    Returns:
        A formatted string with temperature, weather condition, and humidity.
    """
    if not settings.openweather_api_key:
        return "⚠️ Weather service is not configured (missing API key)."

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": settings.openweather_api_key,
            "units": "metric",
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)

        if response.status_code == 404:
            return f"❌ City '{city}' not found. Please check the spelling."

        response.raise_for_status()
        data = response.json()

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        condition = data["weather"][0]["description"].title()
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        return (
            f"🌍 Weather in {city.title()}:\n"
            f"🌡️ Temperature: {temp}°C (feels like {feels_like}°C)\n"
            f"☁️ Condition: {condition}\n"
            f"💧 Humidity: {humidity}%\n"
            f"💨 Wind Speed: {wind_speed} m/s"
        )

    except httpx.TimeoutException:
        return f"⏳ Weather request for '{city}' timed out. Please try again."
    except httpx.HTTPStatusError as exc:
        return f"⚠️ Weather API error (HTTP {exc.response.status_code}). Please try again."
    except Exception as exc:
        return f"⚠️ Could not fetch weather for '{city}'. Error: {exc}"
