filepath = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\backend\api\routes\candidates.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix extra blank lines between end of shortlist_candidate and start of shortlist_candidates_bulk
old = '"communication_created": existing_comm is None\n }\n\n\n@router.post("/applications/shortlist-bulk")'
new = '"communication_created": existing_comm is None\n}\n\n@router.post("/applications/shortlist-bulk")'

if old in content:
    content = content.replace(old, new, 1)
    print("Fixed extra blank lines between functions")
else:
    print("Pattern not found")
    idx = content.find('communication_created')
    if idx >= 0:
        print(f"Context: {repr(content[idx:idx+120])}")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
