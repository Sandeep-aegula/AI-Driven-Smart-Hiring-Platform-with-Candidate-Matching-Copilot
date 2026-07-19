import streamlit as st
import os
import sys
import time

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.components.page_utils import setup_page, render_sidebar_footer
from frontend.services.ai_service import get_client as get_ollama_client

# Page Config
st.set_page_config(
    page_title="AI Copilot - HirePilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

setup_page("AI Copilot", "ChatGPT-style floating recruitment assistant powered by local Ollama", page_key=__file__)

# Chat Session initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am HirePilot's AI Copilot, running locally on `qwen2.5-coder:7b`. Tap **+** for quick actions or ask me any recruitment question."}
    ]

# --- QUICK ACTIONS (live inside the "+" button on the input bar) ---
QUICK_ACTIONS = {
    "🪄 Generate JD": "Write a complete job description for a Lead React Frontend Developer role.",
    "📄 Summarize Resume": "Summarize the key experience and technical strengths of a Python developer with 6 years experience.",
    "👥 Compare Candidates": "Provide a checklist on how to compare technical candidates side-by-side.",
    "🥇 Recommend Candidate": "Write a recommendation email advancing candidate 'Sarah Jenkins' to the final interview round.",
    "❓ Generate Questions": "Generate 4 coding interview questions on FastAPI and Docker.",
    "📈 Hiring Report": "Draft a summary recruitment metric report including application conversion numbers.",
}


# =========================================================================
# CUSTOM PILL-SHAPED CHAT INPUT (inlined — no separate component file)
# =========================================================================
def _inject_copilot_input_css():
    st.markdown(
        """
        <style>
        .copilot-input-wrapper {
            position: sticky;
            bottom: 0;
            background: transparent;
            padding: 12px 0 8px 0;
            z-index: 100;
        }
        .copilot-input-wrapper [data-testid="stHorizontalBlock"] {
            background-color: #1e1e1e;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 9999px;
            padding: 8px 12px;
            align-items: center;
            gap: 8px;
        }
        /* "+" quick-actions button */
        .copilot-input-wrapper div[data-testid="stPopover"] button {
            border-radius: 50% !important;
            width: 36px !important;
            height: 36px !important;
            padding: 0 !important;
            background-color: transparent !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            color: rgba(255, 255, 255, 0.8) !important;
            font-size: 18px !important;
            line-height: 1 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        .copilot-input-wrapper div[data-testid="stPopover"] button:hover {
            background-color: rgba(255, 255, 255, 0.1) !important;
            border-color: rgba(255, 255, 255, 0.25) !important;
        }
        /* Popover content styling */
        .copilot-input-wrapper [data-testid="stPopover"] > div > div {
            background-color: #2a2a2a !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            padding: 8px !important;
        }
        .copilot-input-wrapper [data-testid="stPopover"] button {
            border-radius: 8px !important;
            background-color: transparent !important;
            border: none !important;
            color: #e6e6e6 !important;
            font-size: 14px !important;
            padding: 10px 12px !important;
            width: 100% !important;
            text-align: left !important;
            height: auto !important;
        }
        .copilot-input-wrapper [data-testid="stPopover"] button:hover {
            background-color: rgba(255, 106, 61, 0.15) !important;
            color: #ff6a3d !important;
        }
        /* Text input — borderless, transparent, sits in the middle */
        .copilot-input-wrapper .stTextInput > div > div {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        .copilot-input-wrapper .stTextInput input {
            background-color: transparent !important;
            border: none !important;
            color: #e6e6e6 !important;
            font-size: 15px !important;
            padding: 8px 4px !important;
            width: 100% !important;
            min-height: 44px !important;
        }
        .copilot-input-wrapper .stTextInput input:focus {
            box-shadow: none !important;
            outline: none !important;
        }
        .copilot-input-wrapper .stTextInput input::placeholder {
            color: rgba(255, 255, 255, 0.45) !important;
        }
        /* Send button — circular, accent color, dims when disabled */
        .copilot-input-wrapper .send-btn button {
            border-radius: 50% !important;
            width: 36px !important;
            height: 36px !important;
            padding: 0 !important;
            background-color: #ff6a3d !important;
            border: none !important;
            color: #ffffff !important;
            font-size: 16px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        .copilot-input-wrapper .send-btn button:hover {
            background-color: #ff7f57 !important;
        }
        .copilot-input-wrapper .send-btn button:disabled {
            background-color: rgba(255, 106, 61, 0.35) !important;
            color: rgba(255, 255, 255, 0.5) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_copilot_chat_input(key: str, placeholder: str, quick_actions: dict) -> str | None:
    """
    Renders the dark pill-shaped chat input (+ button, borderless text field,
    circular send arrow, no mic icon). Returns the submitted message text
    (already resolved from a quick-action label if one was chosen), or None.
    """
    _inject_copilot_input_css()

    text_key = f"{key}_text"
    if text_key not in st.session_state:
        st.session_state[text_key] = ""

    st.markdown('<div class="copilot-input-wrapper">', unsafe_allow_html=True)
    col_plus, col_input, col_send = st.columns([0.6, 7, 0.6], gap="small")

    with col_plus:
        with st.popover("+", use_container_width=True):
            st.caption("Quick actions")
            for label in quick_actions:
                if st.button(label, key=f"{key}_qa_{label}", use_container_width=True):
                    st.session_state[text_key] = label
                    st.rerun()

    with col_input:
        st.text_input(
            label="copilot_message",
            key=text_key,
            placeholder=placeholder,
            label_visibility="collapsed",
        )

    submitted = False
    with col_send:
        st.markdown('<div class="send-btn">', unsafe_allow_html=True)
        has_text = bool(st.session_state[text_key].strip())
        if st.button("↑", key=f"{key}_send", disabled=not has_text, use_container_width=True):
            submitted = True
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        raw = st.session_state[text_key].strip()
        st.session_state[text_key] = ""
        return quick_actions.get(raw, raw)  # resolve quick-action label -> full prompt

    return None


# =========================================================================
# CHAT DISPLAY + AI HANDLING
# =========================================================================
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def text_streamer(text):
    for token in text.split(" "):
        yield token + " "
        time.sleep(0.015)


def handle_user_message(user_input: str):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("AI is typing..."):
                client = get_ollama_client()
                try:
                    reply = client.generate(
                        user_input,
                        system="You are HirePilot AI Copilot, a senior recruitment coordinator. Respond professionally using clean markdown formatting."
                    )
                except Exception:
                    reply = (
                        f"Ollama connection offline. Fallback preview response for: **{user_input}**\n\n"
                        "I can help write job descriptions, design questions, and compare resumes once the "
                        "Ollama local backend is active on port 11434."
                    )

                response_container = st.empty()
                full_response = ""
                for chunk in text_streamer(reply):
                    full_response += chunk
                    response_container.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": reply})


# --- RENDER THE CUSTOM INPUT AND HANDLE SUBMISSION ---
user_input = render_copilot_chat_input(
    key="copilot_input",
    placeholder="Ask AI Copilot anything...",
    quick_actions=QUICK_ACTIONS,
)

if user_input:
    handle_user_message(user_input)
    st.rerun()