import os

BASE = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot"
files = [
    r"frontend\services\assistant_service.py",
    r"frontend\components\ai_assistant.py",
    r"frontend\components\ai_floating_button.py",
    r"frontend\components\ai_chat_window.py",
    r"frontend\components\ai_header.py",
    r"frontend\components\ai_message.py",
    r"frontend\components\ai_input.py",
    r"frontend\components\ai_sidebar.py",
    r"frontend\components\ai_typing_indicator.py",
    r"frontend\app.py",
]

for rel_path in files:
    filepath = os.path.join(BASE, rel_path)
    if not os.path.exists(filepath):
        print(f"SKIP (not found): {rel_path}")
        continue

    with open(filepath, "rb") as f:
        raw = f.read()

    # Decode with replacement for any bad bytes
    text = raw.decode("utf-8", errors="replace")

    # Normalize all line endings to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove non-printable chars except \n and \t
    cleaned = "".join(ch for ch in text if ch.isprintable() or ch in "\n\t")

    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(cleaned)

    print(f"Fixed: {rel_path} ({len(cleaned)} chars)")

print("Done!")
