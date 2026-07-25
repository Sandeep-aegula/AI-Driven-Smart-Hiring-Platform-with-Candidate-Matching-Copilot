import os

file_path = "frontend/views/ai_copilot.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove the _analyze_resume function
old_func = '''def _analyze_resume(file_text: str, filename: str) -> str:
    """Generate an initial analysis report for the uploaded resume."""
    prompt = (
        "Analyze this resume and provide a structured report with:\\n"
        "1. Candidate Summary\\n"
        "2. Professional Summary\\n"
        "3. Key Skills\\n"
        "4. Work Experience\\n"
        "5. Education\\n"
        "6. Notable Projects\\n"
        "7. Strengths\\n"
        "8. Weaknesses / Gaps\\n"
        "9. ATS Score (1-10)\\n"
        "10. Hiring Recommendation\\n"
        "11. Suggested Interview Questions\\n\\n"
        f"Resume:\\n{file_text[:6000]}"
    )
    return send_message(prompt)


'''

# Remove the broken automatic analysis block
old_block = '''        # Handle automatic analysis after upload
        if st.session_state.get("is_thinking", False):
            messages = get_messages()
            last_user_msg = next(
                (
                    m["content"]
                    for m in reversed(messages)
                    if m["role"] == "user"
                ),
                "",
            )
            # Check if this is an upload notification (not a user question)
            if last_user_msg and "📎 Uploaded resume:" in last_user_msg:
                resume_context = get_resume_context()
                if resume_context:
                    with st.chat_message("assistant", avatar="🤖"):
                        with st.spinner("Analyzing resume..."):
                            analysis = _analyze_resume(
                                resume_context.replace("[Uploaded Resume:", "").replace("]", "").strip(),
                                "uploaded resume"
                            )
                            append_message("assistant", analysis)
                            set_thinking(False)
                            st.rerun()

'''

content = content.replace(old_func, "")
content = content.replace(old_block, "")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Cleanup completed successfully")
