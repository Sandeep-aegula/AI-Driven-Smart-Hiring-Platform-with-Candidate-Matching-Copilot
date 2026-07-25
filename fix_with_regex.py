import os
import re

BASE = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot"
files_to_fix = [
    r"frontend\components\ai_chat_window.py",
    r"frontend\components\ai_header.py",
    r"frontend\components\ai_message.py",
    r"frontend\components\ai_input.py",
    r"frontend\components\ai_sidebar.py",
    r"frontend\components\ai_typing_indicator.py",
]

def fix_with_regex(filepath):
    """Fix a single-line Python file using regex to add line breaks."""
    with open(filepath, "rb") as f:
        raw = f.read()
    
    text = raw.decode("utf-8", errors="replace")
    
    # If already has multiple lines, skip
    if text.count("\n") > 10:
        return False
    
    # Add line breaks before key Python constructs
    # Order matters - do these in sequence
    
    # 1. Add newline after module docstring closing """
    text = re.sub(r'"""\s*(?=\s*[a-zA-Z])', '"""\n\n', text)
    
    # 2. Add newline before import statements
    text = re.sub(r'(?<!\n)(\s*)(import\s)', r'\n\2', text)
    text = re.sub(r'(?<!\n)(\s*)(from\s)', r'\n\2', text)
    
    # 3. Add newline before function/class definitions
    text = re.sub(r'(?<!\n)(\s*)(def\s)', r'\n\n\2', text)
    text = re.sub(r'(?<!\n)(\s*)(class\s)', r'\n\n\2', text)
    
    # 4. Add newline before if/for/while/with/try/except statements
    text = re.sub(r'(?<!\n)(\s*)(if\s)', r'\n\2', text)
    text = re.sub(r'(?<!\n)(\s*)(for\s)', r'\n\2', text)
    text = re.sub(r'(?<!\n)(\s*)(while\s)', r'\n\2', text)
    text = re.sub(r'(?<!\n)(\s*)(with\s)', r'\n\2', text)
    text = re.sub(r'(?<!\n)(\s*)(try\s)', r'\n\2', text)
    text = re.sub(r'(?<!\n)(\s*)(except\s)', r'\n\2', text)
    text = re.sub(r'(?<!\n)(\s*)(return\s)', r'\n\2', text)
    
    # 5. Add double newline before top-level statements
    text = re.sub(r'\n\n\n+', '\n\n', text)  # Clean up multiple newlines
    
    # 6. Fix indentation - add 4 spaces after newlines that should be indented
    # This is tricky, so let's just ensure basic formatting
    
    # Clean up leading whitespace on lines
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            cleaned_lines.append(stripped)
        else:
            cleaned_lines.append('')
    
    text = '\n'.join(cleaned_lines)
    
    # Write back
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    
    return True

for rel_path in files_to_fix:
    filepath = os.path.join(BASE, rel_path)
    if not os.path.exists(filepath):
        print(f"SKIP: {rel_path}")
        continue
    
    print(f"Fixing: {rel_path}")
    if fix_with_regex(filepath):
        print(f"  -> Fixed")
    else:
        print(f"  -> Already had newlines")

print("\nDone!")
