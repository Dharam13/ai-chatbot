"""
Conversational AI Chatbot — Streamlit Frontend
================================================
A clean chat interface that connects to the FastAPI backend.
Features session management, chat history, and a dark-themed UI.

Run:
    python -m streamlit run frontend.py
"""

import uuid
import httpx
import streamlit as st

# ── Configuration ────────────────────────────────────────────
API_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 180.0


# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Atlas AI — Conversational Chatbot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)


# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #0f0c29 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.2);
    }

    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #e0e7ff !important;
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: #a5b4fc !important;
    }

    .chat-header {
        text-align: center;
        padding: 1.5rem 1rem 1rem;
        margin-bottom: 1rem;
    }

    .chat-header h1 {
        background: linear-gradient(135deg, #818cf8 0%, #6366f1 30%, #a78bfa 70%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
        letter-spacing: -0.5px;
    }

    .chat-header p {
        color: #94a3b8;
        font-size: 0.95rem;
        font-weight: 300;
    }

    .stChatMessage {
        border-radius: 16px !important;
        margin-bottom: 0.75rem !important;
        border: 1px solid rgba(99, 102, 241, 0.1) !important;
        backdrop-filter: blur(10px) !important;
    }

    .meta-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 8px;
        flex-wrap: wrap;
    }

    .provider-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .provider-ollama {
        background: linear-gradient(135deg, #064e3b, #065f46);
        color: #6ee7b7;
        border: 1px solid rgba(110, 231, 183, 0.3);
    }

    .provider-groq {
        background: linear-gradient(135deg, #1e3a5f, #1e40af);
        color: #93c5fd;
        border: 1px solid rgba(147, 197, 253, 0.3);
    }

    .tool-badge {
        display: inline-block;
        background: linear-gradient(135deg, #312e81, #4338ca);
        color: #c7d2fe;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        margin: 2px 3px;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }

    .styled-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.3), transparent);
        margin: 1rem 0;
        border: none;
    }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.3); border-radius: 3px; }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }
</style>
""", unsafe_allow_html=True)


# ── Session State ────────────────────────────────────────────

if "session_id" not in st.session_state:
    st.session_state.session_id = f"session-{uuid.uuid4().hex[:8]}"

if "messages" not in st.session_state:
    st.session_state.messages = []


# ── Helper Functions ─────────────────────────────────────────

def send_message(message: str) -> dict | None:
    """Send a message to the FastAPI backend and return the response."""
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.post(
                f"{API_BASE_URL}/chat",
                json={
                    "session_id": st.session_state.session_id,
                    "message": message,
                },
            )

        if response.status_code == 429:
            st.error("⚡ Rate limit exceeded. Please wait a moment.")
            return None
        elif response.status_code == 503:
            st.error("🔌 AI service unavailable. Check backend is running.")
            return None
        elif response.status_code != 200:
            data = response.json()
            st.error(f"❌ Error: {data.get('error', 'Unknown error')}")
            return None

        return response.json()

    except httpx.ConnectError:
        st.error("🔌 Cannot connect to backend. Make sure it's running on `localhost:8000`.")
        return None
    except httpx.TimeoutException:
        st.error("⏳ Request timed out. The AI is taking too long to respond.")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        return None


def get_health() -> dict | None:
    """Fetch health status from the backend."""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{API_BASE_URL}/health")
        return response.json() if response.status_code == 200 else None
    except Exception:
        return None


def clear_session() -> None:
    """Clear chat history both locally and on the backend."""
    try:
        with httpx.Client(timeout=5.0) as client:
            client.delete(f"{API_BASE_URL}/chat/{st.session_state.session_id}")
    except Exception:
        pass
    st.session_state.messages = []


def new_session() -> None:
    """Start a completely new session."""
    clear_session()
    st.session_state.session_id = f"session-{uuid.uuid4().hex[:8]}"


def render_provider_badge(provider: str) -> str:
    """Return HTML for a provider badge."""
    css_class = "provider-ollama" if provider == "ollama" else "provider-groq"
    icon = "🦙" if provider == "ollama" else "⚡"
    return f'<span class="provider-badge {css_class}">{icon} {provider}</span>'


def render_tool_badges(tools: list[str]) -> str:
    """Return HTML for tool usage badges."""
    if not tools:
        return ""
    badges = "".join(f'<span class="tool-badge">🔧 {t}</span>' for t in tools)
    return f'<div class="meta-row">{badges}</div>'


# ── Sidebar ──────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🤖 Atlas AI")
    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    st.markdown("### 📋 Session")
    st.code(st.session_state.session_id, language=None)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            clear_session()
            st.rerun()
    with col2:
        if st.button("🔄 New Session", use_container_width=True):
            new_session()
            st.rerun()

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    st.markdown("### 📡 System Status")
    health = get_health()

    if health:
        providers = health.get("providers", {})
        for name, available in providers.items():
            icon = "🦙" if name == "ollama" else "⚡"
            status_icon = "🟢" if available else "🔴"
            st.markdown(f"{status_icon} {icon} **{name.title()}** — {'Online' if available else 'Offline'}")
        st.markdown(f"👥 Active Sessions: **{health.get('active_sessions', 0)}**")
    else:
        st.markdown("🔴 **Backend Offline**")
        st.code("python -m uvicorn app.main:app --port 8000", language="bash")

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    st.markdown("### 🛠️ Capabilities")
    for icon, name in [("📅", "Date & Time"), ("🌤️", "Weather"), ("📰", "News"), ("🔢", "Calculator"), ("📖", "Wikipedia")]:
        st.markdown(f"{icon} {name}")

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)
    st.caption("Built with FastAPI + LangChain + Streamlit")


# ── Main Chat Area ───────────────────────────────────────────

st.markdown("""
<div class="chat-header">
    <h1>🤖 Atlas AI</h1>
    <p>Your intelligent conversational assistant — powered by LangChain</p>
</div>
""", unsafe_allow_html=True)

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

        if msg["role"] == "assistant" and msg.get("meta"):
            meta = msg["meta"]
            html_parts = []
            if meta.get("llm_provider"):
                html_parts.append(render_provider_badge(meta["llm_provider"]))
            if meta.get("tools_used"):
                html_parts.append(render_tool_badges(meta["tools_used"]))
            if html_parts:
                st.markdown(f'<div class="meta-row">{"".join(html_parts)}</div>', unsafe_allow_html=True)


# ── Chat Input ───────────────────────────────────────────────

prompt = st.chat_input("Ask Atlas anything...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🧠 Thinking..."):
            response = send_message(prompt)

        if response:
            reply = response.get("reply", "Sorry, I couldn't generate a response.")
            provider = response.get("llm_provider", "unknown")
            tools_used = response.get("tools_used", [])

            st.markdown(reply)

            html_parts = [render_provider_badge(provider)]
            if tools_used:
                html_parts.append(render_tool_badges(tools_used))
            st.markdown(f'<div class="meta-row">{"".join(html_parts)}</div>', unsafe_allow_html=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": reply,
                "meta": {"llm_provider": provider, "tools_used": tools_used},
            })
        else:
            fallback = "I encountered an error. Please try again."
            st.markdown(fallback)
            st.session_state.messages.append({"role": "assistant", "content": fallback, "meta": {}})
