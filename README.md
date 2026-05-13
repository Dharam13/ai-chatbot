# 🤖 Conversational AI Chatbot

A **production-grade conversational AI chatbot** backend built with FastAPI and LangChain. Features automatic LLM fallback, tool-calling agents, session-based memory, rate limiting, and LangSmith observability.

---

## ✨ Features

| Feature | Description |
|---|---|
| **LLM Fallback** | Ollama (local) -> Groq (cloud) automatic failover |
| **Conversational Memory** | Per-session chat history stored in memory |
| **Tool-Calling Agent** | DateTime, Weather, News, Calculator, Wikipedia |
| **Rate Limiting** | 20 req/min/session sliding-window limiter |
| **LangSmith Tracing** | Full observability with token tracking |
| **Global Error Handling** | Structured JSON errors with custom exception classes |
| **Async Everything** | All endpoints are fully async |
| **Streamlit Frontend** | Premium dark-themed chat UI with session management |

---

## 📁 Project Structure

```
ai-chatbot/
├── app/
│   ├── __init__.py            # Package metadata
│   ├── main.py                # FastAPI entry point, middleware, error handlers
│   ├── config.py              # Pydantic BaseSettings (env var management)
│   ├── exceptions.py          # Custom exception hierarchy
│   ├── core/
│   │   ├── __init__.py
│   │   ├── llm.py             # LLM provider manager with fallback logic
│   │   ├── memory.py          # Session-scoped conversation memory
│   │   ├── agent.py           # LangChain agent builder + executor
│   │   └── rate_limiter.py    # Sliding-window rate limiter
│   ├── tools/
│   │   ├── __init__.py        # Tool registry (ALL_TOOLS list)
│   │   ├── datetime_tool.py   # Current date/time/day
│   │   ├── weather_tool.py    # OpenWeatherMap integration
│   │   ├── news_tool.py       # NewsAPI headlines
│   │   ├── calculator_tool.py # AST-based safe math evaluator
│   │   └── wikipedia_tool.py  # Wikipedia summaries
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── system.py          # System prompt template (ChatPromptTemplate)
│   └── routes/
│       ├── __init__.py
│       └── chat.py            # Chat API endpoints
├── frontend.py                # Streamlit chat UI
├── .env.example               # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & Navigate

```bash
cd ai-chatbot
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

### 5. Start Ollama (optional, for local LLM)

```bash
ollama serve
ollama pull llama3.2:3b
```

### 6. Run the Backend

```bash
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 7. Run the Frontend (new terminal)

```bash
python -m streamlit run frontend.py
```

The Streamlit UI will open at **http://localhost:8501**

---

## 📡 API Endpoints

### `POST /chat` — Send a Message

**Request:**
```json
{
  "session_id": "user-abc-123",
  "message": "What's the weather in London?"
}
```

**Response:**
```json
{
  "session_id": "user-abc-123",
  "reply": "🌍 Weather in London:\n🌡️ Temperature: 15°C...",
  "llm_provider": "ollama",
  "tools_used": ["get_weather"],
  "suggestions": [
    "What's the forecast for tomorrow?",
    "How does London's weather compare to Paris?"
  ]
}
```

### `DELETE /chat/{session_id}` — Clear Session

```bash
curl -X DELETE http://localhost:8000/chat/user-abc-123
```

**Response:**
```json
{
  "session_id": "user-abc-123",
  "status": "Session cleared successfully"
}
```

### `GET /chat/{session_id}/history` — Get History

```bash
curl http://localhost:8000/chat/user-abc-123/history
```

**Response:**
```json
{
  "session_id": "user-abc-123",
  "history": [
    { "role": "user", "content": "Hello!" },
    { "role": "assistant", "content": "Hi there! How can I help?..." }
  ],
  "message_count": 2
}
```

### `GET /health` — Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "providers": {
    "ollama": true,
    "groq": true
  },
  "active_sessions": 3
}
```

---

## 🔧 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `OLLAMA_BASE_URL` | Ollama server URL | No (default: `http://localhost:11434`) |
| `OLLAMA_MODEL` | Ollama model name | No (default: `llama3.2:3b`) |
| `OLLAMA_TIMEOUT` | Ollama request timeout (seconds) | No (default: `15`) |
| `GROQ_API_KEY` | Groq API key | Yes (for fallback) |
| `GROQ_MODEL` | Groq model name | No (default: `llama-3.1-8b-instant`) |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | Yes (for weather tool) |
| `NEWS_API_KEY` | Newsdata.io API key | Yes (for news tool) |
| `LANGCHAIN_API_KEY` | LangSmith API key | Optional |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith tracing | No (default: `true`) |
| `LANGCHAIN_PROJECT` | LangSmith project name | No (default: `conversational-ai-chatbot`) |
| `RATE_LIMIT_PER_MINUTE` | Max requests per session/minute | No (default: `20`) |

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────────────────────────────┐
│  Streamlit UI   │────▶│  FastAPI (main.py)                        │
│  (frontend.py)  │     │  ├── CORS Middleware                      │
│  Port 8501      │     │  ├── Global Exception Handlers            │
└─────────────────┘     │  └── Rate Limiter Check                   │
                        └──────────────┬────────────────────────────┘
                                       │
                        ┌──────────────▼────────────────────────────┐
                        │  Agent (core/agent.py)                    │
                        │  ├── LLM Selection (Ollama -> Groq)        │
                        │  ├── System Prompt (prompts/system.py)    │
                        │  ├── Chat History (core/memory.py)        │
                        │  └── AgentExecutor                        │
                        │      ├── DateTime Tool                    │
                        │      ├── Weather Tool (OpenWeatherMap)     │
                        │      ├── News Tool (NewsAPI)              │
                        │      ├── Calculator Tool (AST-based)      │
                        │      └── Wikipedia Tool                   │
                        └──────────────┬────────────────────────────┘
                                       │
                        ┌──────────────▼────────────────────────────┐
                        │  LangSmith (Observability)                │
                        │  └── Traces, token usage, latency         │
                        └───────────────────────────────────────────┘
```

---

## 🛡️ Error Handling

All errors return structured JSON:

```json
{
  "error": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE"
}
```

| HTTP Code | Error Code | Meaning |
|---|---|---|
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests for this session |
| 503 | `LLM_UNAVAILABLE` | Neither Ollama nor Groq is reachable |
| 500 | `TOOL_FAILURE` | A tool encountered an error |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

---

## 📝 License

This project is for educational and personal use.
