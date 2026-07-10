import streamlit as st
import os
import sys
import time

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

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
        {"role": "assistant", "content": "Hello! I am HirePilot's AI Copilot, running locally on `qwen2.5-coder:7b`. Select a quick action below or ask me any recruitment questions."}
    ]

# --- QUICK PROMPT ROW ---
st.markdown("##### Quick Prompts:")
q_cols = st.columns(6)
prompt_trigger = None

with q_cols[0]:
    if st.button("🪄 Generate JD", use_container_width=True):
        prompt_trigger = "Write a complete job description for a Lead React Frontend Developer role."
with q_cols[1]:
    if st.button("📄 Summarize Resume", use_container_width=True):
        prompt_trigger = "Summarize the key experience and technical strengths of a Python developer with 6 years experience."
with q_cols[2]:
    if st.button("👥 Compare Candidates", use_container_width=True):
        prompt_trigger = "Provide a checklist on how to compare technical candidates side-by-side."
with q_cols[3]:
    if st.button("🥇 Recommend Candidate", use_container_width=True):
        prompt_trigger = "Write an recommendation email advancing candidate 'Sarah Jenkins' to the final interview round."
with q_cols[4]:
    if st.button("❓ Generate Questions", use_container_width=True):
        prompt_trigger = "Generate 4 coding interview questions on FastAPI and Docker."
with q_cols[5]:
    if st.button("📈 Hiring Report", use_container_width=True):
        prompt_trigger = "Draft a summary recruitment metric report including application conversion numbers."

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Display chat history in clean container
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Text Streaming Simulator for typing animations
def text_streamer(text):
    for token in text.split(" "):
        yield token + " "
        time.sleep(0.015)

# Handle triggers
user_input = st.chat_input("Message AI Copilot...")

if prompt_trigger:
    user_input = prompt_trigger

if user_input:
    # Display user bubble
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("AI is typing..."):
            client = get_ollama_client()
            try:
                reply = client.generate(
                    user_input, 
                    system="You are HirePilot AI Copilot, a senior recruitment coordinator. Respond professionally using clean markdown formatting."
                )
            except Exception:
                reply = f"Ollama connection offline. Fallback preview response for: **{user_input}**\n\nI can help write job descriptions, design questions, and compare resumes once the Ollama local backend is active on port 11434."
            
            # Stream response back
            response_container = st.empty()
            full_response = ""
            for chunk in text_streamer(reply):
                full_response += chunk
                response_container.markdown(full_response)
                
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# Sidebar footer is rendered by setup_page()
