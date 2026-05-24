import time
import uuid
import streamlit as st
from core.llm import get_agent

# ─── Page Config ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Museum Chatbot",
    page_icon="🏛️",
    layout="centered",
)

# ─── Custom Styling ──────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Google Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    *, html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }

    /* ── New Chat Button ── */
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background: linear-gradient(135deg, #e94560, #c23152) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.55rem 1rem !important;
        font-weight: 600 !important;
        width: 100%;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(233, 69, 96, 0.4) !important;
    }

    /* ── Chat messages ── */
    .stChatMessage {
        border-radius: 12px !important;
        margin-bottom: 0.5rem !important;
    }

    /* ── Chat input ── */
    .stChatInput > div {
        border-radius: 12px !important;
    }

    /* ── Header ── */
    .main-header {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    .main-header h1 {
        font-size: 1.75rem;
        font-weight: 700;
        background: linear-gradient(135deg, #e94560, #0f3460);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .main-header p {
        color: #888;
        font-size: 0.9rem;
    }

    /* ── Timer badge ── */
    .timer-badge {
        display: inline-block;
        font-size: 0.72rem;
        color: #888;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ─────────────────────────────────────────
if "agent" not in st.session_state:
    st.session_state.agent = get_agent()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []


# ─── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏛️ Museum Chatbot")
    st.caption("AI-powered museum info & ticketing")
    st.divider()

    if st.button("✨ New Chat", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown(
        f"<small>🧵 Thread: <code>{st.session_state.thread_id[:8]}…</code></small>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<small>🤖 Model: <code>llama3.2</code> (local)</small>",
        unsafe_allow_html=True,
    )


# ─── Main Chat Area ─────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown(
        """
        <div class="main-header">
            <h1>🏛️ Museum Chatbot</h1>
            <p>Search museums · Get details · Book tickets</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "time" in msg:
            st.markdown(
                f'<span class="timer-badge">⏱️ {msg["time"]:.2f}s</span>',
                unsafe_allow_html=True,
            )


# ─── Chat Input ─────────────────────────────────────────────────
if user_input := st.chat_input("Ask me about museums…"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get bot response
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            start = time.perf_counter()
            response = st.session_state.agent.invoke(
                {"messages": [("user", user_input)]},
                config=config,
            )
            elapsed = time.perf_counter() - start

            bot_msg = response["messages"][-1].content
            st.markdown(bot_msg)
            st.markdown(
                f'<span class="timer-badge">⏱️ {elapsed:.2f}s</span>',
                unsafe_allow_html=True,
            )

    st.session_state.messages.append(
        {"role": "assistant", "content": bot_msg, "time": elapsed}
    )
