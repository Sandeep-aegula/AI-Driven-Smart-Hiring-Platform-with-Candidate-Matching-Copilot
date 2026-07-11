"""
components/ai_copilot.py — HirePilot AI Copilot Chat Page
"""
import time
import streamlit as st
from services.cache import get_ollama_client


def render_ai_copilot() -> None:
    if "messages" not in st.session_state or not st.session_state["messages"]:
        st.session_state["messages"] = [{
            "role": "assistant",
            "content": ("Hello! I'm HirePilot's AI Copilot, running locally on "
                        "`qwen2.5-coder:7b`. Select a quick action or ask anything "
                        "about recruitment, resumes, or hiring strategy.")
        }]

    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        🤖 AI Copilot
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        ChatGPT-style recruitment assistant powered by local Ollama
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

    # ── Quick Prompts ─────────────────────────────────────────────────────
    st.markdown("##### ⚡ Quick Prompts:")
    q = st.columns(6)
    prompt_trigger = None

    prompts = [
        ("🪄 Generate JD",       "Write a complete job description for a Lead React Frontend Developer role."),
        ("📄 Summarize Resume",  "Summarize the key technical strengths of a Python developer with 6 years experience."),
        ("👥 Compare Candidates","Provide a structured comparison checklist for evaluating two technical candidates."),
        ("🥇 Recommend",         "Write a recommendation email advancing candidate 'Sarah Jenkins' to the final round."),
        ("❓ Interview Qs",       "Generate 4 coding interview questions on FastAPI and Docker."),
        ("📈 Hiring Report",      "Draft a summary recruitment metric report including application conversion numbers."),
    ]
    for col, (label, prompt) in zip(q, prompts):
        with col:
            if st.button(label, use_container_width=True, key=f"qp_{label}"):
                prompt_trigger = prompt

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # ── Chat History ──────────────────────────────────────────────────────
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ── Input ─────────────────────────────────────────────────────────────
    user_input = st.chat_input("Message AI Copilot…")
    if prompt_trigger:
        user_input = prompt_trigger

    if user_input:
        st.session_state["messages"].append({"role":"user","content":user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("AI is thinking…"):
                client = get_ollama_client()
                try:
                    if client:
                        reply = client.generate(
                            user_input,
                            system="You are HirePilot AI Copilot, a senior recruitment coordinator. "
                                   "Respond professionally using clean markdown formatting."
                        )
                    else:
                        raise ConnectionError("Ollama offline")
                except Exception:
                    reply = (
                        f"⚠️ Ollama connection offline. Fallback preview for: **{user_input}**\n\n"
                        "I can help write job descriptions, design questions, and compare resumes "
                        "once the Ollama local backend is active on port **11434**."
                    )

            response_container = st.empty()
            full_response = ""
            for chunk in _stream(reply):
                full_response += chunk
                response_container.markdown(full_response)

        st.session_state["messages"].append({"role":"assistant","content":reply})
        st.rerun()

    # ── Clear Chat ────────────────────────────────────────────────────────
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    if len(st.session_state["messages"]) > 1:
        if st.button("🗑️ Clear Chat History", type="secondary"):
            st.session_state["messages"] = [st.session_state["messages"][0]]
            st.rerun()


def _stream(text: str):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.012)
