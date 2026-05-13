"""
Application Configuration
=========================
Centralized configuration using Pydantic BaseSettings.
All environment variables are loaded from .env and validated at startup.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        ollama_base_url:    Base URL for the local Ollama instance.
        ollama_model:       Model name to use with Ollama (e.g., "llama3.2:3b").
        ollama_timeout:     Connection timeout in seconds for Ollama requests.
        enable_groq_fallback: Whether to use Groq when Ollama is unavailable.
        groq_api_key:       Groq API key (optional fallback provider).
        groq_model:         Model name for Groq.
        openweather_api_key: API key for OpenWeatherMap.
        news_api_key:       API key for Newsdata.io.
        langchain_api_key:  API key for LangSmith tracing.
        langchain_tracing_v2: Enable LangSmith v2 tracing.
        langchain_project:  LangSmith project name for trace grouping.
        rate_limit_per_minute: Max requests allowed per session per minute.
    """

    # --- Ollama (Primary LLM) ---
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for the Ollama API server",
    )
    ollama_model: str = Field(
        default="llama3.2:3b",
        description="Ollama model identifier",
    )
    ollama_timeout: int = Field(
        default=15,
        description="Timeout in seconds for Ollama requests",
    )

    # --- Groq (Optional Cloud Fallback LLM) ---
    enable_groq_fallback: bool = Field(
        default=True,
        description="Use Groq when Ollama is unavailable",
    )
    groq_api_key: str = Field(
        default="",
        description="Groq API key",
    )
    groq_model: str = Field(
        default="llama-3.1-8b-instant",
        description="Groq model identifier",
    )

    # --- External Tool APIs ---
    openweather_api_key: str = Field(
        default="",
        description="OpenWeatherMap API key for weather tool",
    )
    news_api_key: str = Field(
        default="",
        description="Newsdata.io API key for news headlines tool",
    )

    # --- LangSmith Observability ---
    langchain_api_key: str = Field(
        default="",
        description="LangSmith API key for tracing",
    )
    langchain_tracing_v2: bool = Field(
        default=True,
        description="Enable LangSmith v2 tracing",
    )
    langchain_project: str = Field(
        default="conversational-ai-chatbot",
        description="LangSmith project name",
    )

    # --- Rate Limiting ---
    rate_limit_per_minute: int = Field(
        default=20,
        description="Maximum requests per session per minute",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


# ── Singleton instance ──────────────────────────────────────
# Import `settings` anywhere in the app to access configuration.
settings = Settings()
