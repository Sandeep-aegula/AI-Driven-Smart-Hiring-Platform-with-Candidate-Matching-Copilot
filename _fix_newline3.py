filepath = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\backend\api\routes\candidates.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the exact pattern: remove space before } and reduce blank lines
old = '"communication_created": existing_comm is None\n }\n\n\n@router.post("/applications/shortlist-bulk")'
new = '"communication_created": existing_comm is None\n}\n\n@router.post("/applications/shortlist-bulk")'

if old in content:
    content = content.replace(old, new, 1)
    print("Fixed spacing between functions")
else:
    print("Pattern not found - let me show exact bytes")
    idx = content.find('communication_created')
    if idx >= 0:
        # Show hex of the area
        snippet = content[idx:idx+80]
        print(f"Hex: {snippet.encode('utf-8').hex()}")
        print(f"Repr: {repr(snippet)}")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
