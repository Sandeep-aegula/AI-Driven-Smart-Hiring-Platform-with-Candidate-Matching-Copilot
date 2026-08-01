with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

old = """    else:
        st.error(f"View not found! {page}")
# --- RENDER AI ASSISTANT (Floating Chat Widget) ---
render_ai_assistant()
if __name__ == "__main__":
    main()"""

new = """    else:
        st.error(f"View not found! {page}")

    # --- RENDER AI ASSISTANT (Floating Chat Widget) ---
    render_ai_assistant()

if __name__ == "__main__":
    main()"""

if old in content:
    content = content.replace(old, new)
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed: render_ai_assistant moved inside main()")
else:
    print("Pattern not found, checking actual content...")
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "render_ai_assistant" in line:
            print(f"Line {i}: {repr(line)}")
            for j in range(max(0, i - 3), min(len(lines), i + 3)):
                print(f"  {j}: {repr(lines[j])}")
