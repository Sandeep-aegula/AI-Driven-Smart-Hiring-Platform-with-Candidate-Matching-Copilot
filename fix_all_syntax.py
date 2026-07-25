import os
import re

BASE = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot"

files_to_fix = {
    r"frontend\components\ai_floating_button.py": "ai_floating_button_fixed.py",
    r"frontend\components\ai_chat_window.py": "ai_chat_window_fixed.py",
    r"frontend\components\ai_header.py": "ai_header_fixed.py",
    r"frontend\components\ai_message.py": "ai_message_fixed.py",
    r"frontend\components\ai_input.py": "ai_input_fixed.py",
    r"frontend\components\ai_sidebar.py": "ai_sidebar_fixed.py",
    r"frontend\components\ai_typing_indicator.py": "ai_typing_indicator_fixed.py",
    r"frontend\components\ai_assistant.py": "ai_assistant_fixed.py",
    r"frontend\services\assistant_service.py": "assistant_service_fixed.py",
    r"frontend\app.py": "app_fixed.py",
}

for rel_path, fixed_name in files_to_fix.items():
    filepath = os.path.join(BASE, rel_path)
    if not os.path.exists(filepath):
        print(f"SKIP (not found): {rel_path}")
        continue

    with open(filepath, "rb") as f:
        raw = f.read()

    # Decode with replacement
    text = raw.decode("utf-8", errors="replace")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # If the file is a single line (no newlines), we need to add them
    if "\n" not in text:
        print(f"Single-line file detected: {rel_path}")
        # Use Python's tokenize to properly format
        import tokenize
        import io

        try:
            tokens = tokenize.generate_tokens(io.StringIO(text).readline)
            formatted_lines = []
            indent_level = 0
            for tok_type, tok_string, tok_start, tok_end, tok_line in tokens:
                if tok_string in [":", "def", "class", "if", "else", "elif", "for", "while", "try", "except", "finally", "with", "return", "import", "from"]:
                    # These often start new lines
                    if formatted_lines and formatted_lines[-1].strip():
                        formatted_lines.append("")
                formatted_lines.append(tok_string)
                if tok_string == ":":
                    indent_level += 1
                elif tok_string in ["def", "class"]:
                    pass

            formatted = " ".join(formatted_lines)
            # This is a rough approach - let's try a simpler one
        except Exception as e:
            print(f"  Tokenize failed: {e}")
            formatted = text

    # Write back with proper newlines
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    print(f"Processed: {rel_path}")

print("Done!")
