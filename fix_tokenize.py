import os
import tokenize
import io

BASE = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot"
files_to_fix = [
    r"frontend\components\ai_chat_window.py",
    r"frontend\components\ai_header.py",
    r"frontend\components\ai_message.py",
    r"frontend\components\ai_input.py",
    r"frontend\components\ai_sidebar.py",
    r"frontend\components\ai_typing_indicator.py",
]

def fix_with_tokenize(filepath):
    """Fix a broken Python file using tokenize.untokenize."""
    with open(filepath, "rb") as f:
        raw = f.read()
    
    text = raw.decode("utf-8", errors="replace")
    
    # Tokenize the broken code
    tokens = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            tokens.append(tok)
    except tokenize.TokenError as e:
        print(f"  Tokenize error: {e}")
        return False
    
    # Untokenize - this adds proper spacing and newlines
    try:
        fixed = tokenize.untokenize(tokens)
    except Exception as e:
        print(f"  Untokenize error: {e}")
        return False
    
    # Write back
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(fixed)
    
    return True

for rel_path in files_to_fix:
    filepath = os.path.join(BASE, rel_path)
    if not os.path.exists(filepath):
        print(f"SKIP: {rel_path}")
        continue
    
    print(f"Fixing: {rel_path}")
    if fix_with_tokenize(filepath):
        print(f"  -> Fixed with tokenize")
    else:
        print(f"  -> Failed")

print("\nDone!")
