import streamlit as st
import os
import sys
import time
from datetime import datetime

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.components.page_utils import setup_page, render_sidebar_footer
from frontend.services.ai_service import get_client as get_ollama_client
from frontend.components.header import render_header
from frontend.components.sidebar import render_sidebar

# Page Config
st.set_page_config(
    page_title="AI Copilot - HirePilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

setup_page("AI Copilot", "Context-aware recruitment assistant powered by local Ollama", page_key=__file__)

# Load custom CSS for AI Copilot
def load_ai_copilot_css():
    css_path = os.path.join(project_root, "frontend", "styles", "ai_copilot.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_ai_copilot_css()

# =========================================================================
# SESSION STATE INITIALIZATION
# =========================================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am HirePilot's AI Copilot, running locally on `qwen2.5-coder:7b`. Tap **+** for quick actions or ask me any recruitment question."}
    ]

if "pending_user_message" not in st.session_state:
    st.session_state.pending_user_message = None

if "uploaded_file_info" not in st.session_state:
    st.session_state.uploaded_file_info = None

if "show_file_chip" not in st.session_state:
    st.session_state.show_file_chip = False

# =========================================================================
# QUICK ACTIONS
# =========================================================================

QUICK_ACTIONS = {
    "🪄 Generate JD": "Write a complete job description for a Lead React Frontend Developer role.",
    "📄 Summarize Resume": "Summarize the key experience and technical strengths of a Python developer with 6 years experience.",
    "👥 Compare Candidates": "Provide a checklist on how to compare technical candidates side-by-side.",
    "🥇 Recommend Candidate": "Write a recommendation email advancing candidate 'Sarah Jenkins' to the final interview round.",
    "❓ Generate Questions": "Generate 4 coding interview questions on FastAPI and Docker.",
    "📈 Hiring Report": "Draft a summary recruitment metric report including application conversion numbers.",
}

# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def text_streamer(text):
    for token in text.split(" "):
        yield token + " "
        time.sleep(0.015)


def handle_user_message(user_input: str):
    """Process user message and get AI response - preserves all backend logic"""
    st.session_state.messages.append({"role": "user", "content": user_input})
    
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
    
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()


def format_timestamp():
    """Format current time as HH:MM"""
    return datetime.now().strftime("%H:%M")


# =========================================================================
# HANDLE PENDING MESSAGE (from quick actions or form submission)
# =========================================================================

if st.session_state.pending_user_message:
    user_input = st.session_state.pending_user_message
    st.session_state.pending_user_message = None
    handle_user_message(user_input)

# =========================================================================
# MAIN PAGE LAYOUT
# =========================================================================

# Page wrapper
st.markdown('<div class="ai-copilot-page">', unsafe_allow_html=True)

# Title Section
st.markdown('''
<div class="ai-copilot-title-section">
    <h1 class="ai-copilot-title">AI Copilot</h1>
    <p class="ai-copilot-subtitle">Context-aware recruitment assistant powered by local Ollama</p>
</div>
''', unsafe_allow_html=True)

# Quick Prompt Cards
st.markdown('<div class="ai-copilot-quick-prompts">', unsafe_allow_html=True)
cols = st.columns(len(QUICK_ACTIONS), gap="small")
for i, (label, prompt) in enumerate(QUICK_ACTIONS.items()):
    with cols[i]:
        icon_char = label[0] if label else "💡"
        clean_label = label[2:] if len(label) > 2 else label
        if st.button(
            f"{icon_char} {clean_label}",
            key=f"quick_action_{i}",
            use_container_width=True,
            help=prompt
        ):
            st.session_state.pending_user_message = prompt
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# Chat Container
st.markdown('<div class="ai-copilot-chat-container">', unsafe_allow_html=True)

# Conversation Area (scrollable)
st.markdown('<div class="ai-copilot-conversation" id="copilot-conversation">', unsafe_allow_html=True)

# Render messages using Streamlit's native chat_message
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
        st.markdown(message["content"])

st.markdown('</div>', unsafe_allow_html=True)

# File upload chip (shown when file is selected)
if st.session_state.show_file_chip and st.session_state.uploaded_file_info:
    file_info = st.session_state.uploaded_file_info
    st.markdown(f'''
    <div class="ai-copilot-file-chip">
        <span class="ai-copilot-file-chip-name">📄 {file_info["name"]}</span>
        <span class="ai-copilot-file-chip-status">✓ Uploaded</span>
        <button class="ai-copilot-file-chip-remove" onclick="this.parentElement.style.display='none';">✕</button>
    </div>
    ''', unsafe_allow_html=True)

# Chat Input Bar - Using Streamlit's native chat_input
st.markdown('<div class="ai-copilot-input-bar">', unsafe_allow_html=True)

# Hidden file uploader (triggered by attachment button)
st.markdown('<div class="ai-copilot-hidden-uploader">', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Upload Resume",
    type=["pdf", "docx", "doc", "txt"],
    key="copilot_resume_uploader",
    label_visibility="collapsed"
)
st.markdown('</div>', unsafe_allow_html=True)

# Handle uploaded file
if uploaded_file is not None:
    st.session_state.uploaded_file_info = {
        "name": uploaded_file.name,
        "type": uploaded_file.type,
        "size": uploaded_file.size
    }
    st.session_state.show_file_chip = True
    # Add file info to chat
    st.session_state.messages.append({
        "role": "user", 
        "content": f"📎 Uploaded resume: **{uploaded_file.name}** ({uploaded_file.type})"
    })
    st.rerun()

# Chat input with attachment button
# We use a custom approach: columns for attachment + input + send
col_attach, col_input, col_send = st.columns([0.08, 0.84, 0.08], gap="small")

with col_attach:
    # Attachment button that triggers the hidden file uploader
    if st.button("📎", key="attach_btn", help="Attach file", use_container_width=True):
        # This will be handled by JavaScript to click the hidden file input
        pass

with col_input:
    # Use chat_input for the main input - but we need custom styling
    # We'll use a text_area with custom CSS for multiline support
    user_input = st.text_area(
        "Chat input",
        key="chat_input_field",
        placeholder="Ask HirePilot anything about jobs, candidates, resumes, interviews...",
        label_visibility="collapsed",
        height=68,
        max_chars=4000
    )

with col_send:
    send_clicked = st.button("➤", key="send_btn", use_container_width=True, disabled=not user_input.strip())

st.markdown('</div>', unsafe_allow_html=True)  # Close input bar
st.markdown('</div>', unsafe_allow_html=True)  # Close chat container
st.markdown('</div>', unsafe_allow_html=True)  # Close page wrapper

# =========================================================================
# HANDLE SEND BUTTON
# =========================================================================

if send_clicked and user_input.strip():
    st.session_state.pending_user_message = user_input.strip()
    # Clear the input field by rerunning
    st.rerun()

# =========================================================================
# JAVASCRIPT FOR INTERACTIVITY
# =========================================================================

st.markdown('''
<script>
// Auto-scroll conversation to bottom on load
document.addEventListener('DOMContentLoaded', function() {
    const conversation = document.getElementById('copilot-conversation');
    if (conversation) {
        conversation.scrollTop = conversation.scrollHeight;
    }
    
    // Attach button triggers hidden file uploader
    const attachBtn = document.querySelector('[data-testid="stButton"] button[key="attach_btn"]');
    const fileUploader = document.querySelector('.ai-copilot-hidden-uploader input[type="file"]');
    
    if (attachBtn && fileUploader) {
        attachBtn.addEventListener('click', function(e) {
            e.preventDefault();
            fileUploader.click();
        });
    }
    
    // Enter key handling for text_area
    const textArea = document.querySelector('.ai-copilot-input-bar textarea');
    const sendBtn = document.querySelector('[data-testid="stButton"] button[key="send_btn"]');
    
    if (textArea && sendBtn) {
        textArea.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (this.value.trim()) {
                    sendBtn.click();
                }
            }
        });
        
        // Auto-resize textarea
        textArea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 150) + 'px';
        });
    }
});
</script>
''', unsafe_allow_html=True)