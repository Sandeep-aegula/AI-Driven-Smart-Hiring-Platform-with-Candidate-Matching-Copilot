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

def fix_single_line_file(filepath):
    """Fix a single-line Python file by adding proper line breaks."""
    with open(filepath, "rb") as f:
        raw = f.read()
    
    text = raw.decode("utf-8", errors="replace")
    
    # Use tokenize to parse and reformat
    tokens = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            tokens.append(tok)
    except tokenize.TokenError as e:
        print(f"  Tokenize error: {e}")
        return False
    
    # Reconstruct with line breaks
    lines = []
    current_line = []
    indent_level = 0
    
    for tok_type, tok_string, tok_start, tok_end, tok_line in tokens:
        if tok_type == tokenize.ENDMARKER:
            if current_line:
                lines.append("".join(current_line))
            break
            
        if tok_type == tokenize.NEWLINE:
            lines.append("".join(current_line))
            current_line = []
            indent_level = 0
        elif tok_type == tokenize.INDENT:
            indent_level += 1
            if current_line:
                lines.append("".join(current_line))
                current_line = []
            lines.append("    " * indent_level)
        elif tok_type == tokenize.DEDENT:
            indent_level = max(0, indent_level - 1)
            if current_line:
                lines.append("".join(current_line))
                current_line = []
            lines.append("    " * indent_level)
        elif tok_type == tokenize.NL:
            # Non-logical newline (inside parentheses)
            if current_line:
                lines.append("".join(current_line))
                current_line = []
                lines.append("    " * (indent_level + 1))
        else:
            current_line.append(tok_string)
    
    formatted = "\n".join(lines)
    
    # Write back
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(formatted)
    
    return True

for rel_path in files_to_fix:
    filepath = os.path.join(BASE, rel_path)
    if not os.path.exists(filepath):
        print(f"SKIP: {rel_path}")
        continue
    
    print(f"Fixing: {rel_path}")
    if fix_single_line_file(filepath):
        print(f"  -> Fixed")
    else:
        print(f"  -> Failed")

print("\nDone!")
