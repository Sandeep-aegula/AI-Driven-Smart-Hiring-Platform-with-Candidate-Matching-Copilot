filepath = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\backend\api\routes\candidates.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Find the first occurrence of the old bulk shortlist function
old_bulk_start = content.find('@router.post("/applications/shortlist-bulk")\nasync def shortlist_candidates_bulk(application_ids: list[int]) -> dict:')
if old_bulk_start == -1:
    print("ERROR: Could not find old bulk shortlist function")
    exit(1)

# Find the next router decorator after the old function (this marks the end)
# Look for the next @router.get or @router.post after the old function
search_start = old_bulk_start + 1
next_decorator = None
for decorator in ['@router.get("/applications/{application_id}")', '@router.get("/applications"', '@router.post("/applications"']:
    pos = content.find(decorator, search_start)
    if pos != -1:
        if next_decorator is None or pos < next_decorator[1]:
            next_decorator = (decorator, pos)

if next_decorator is None:
    print("ERROR: Could not find end of old bulk function")
    exit(1)

decorator_str, decorator_pos = next_decorator
print(f"Found old bulk function at position {old_bulk_start}")
print(f"Next decorator '{decorator_str}' at position {decorator_pos}")

# Remove the old function (including the blank line before the next decorator)
# Keep everything before the old function and everything from the next decorator onwards
new_content = content[:old_bulk_start].rstrip() + "\n\n" + content[decorator_pos:]

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Removed old duplicate bulk shortlist function")
print("Done!")
