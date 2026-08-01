filepath = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\backend\api\routes\candidates.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Find all occurrences of the bulk shortlist decorator
import re
pattern = r'@router\.post\("/applications/shortlist-bulk"\)'
matches = [(m.start(), m.group()) for m in re.finditer(pattern, content)]
print(f"Found {len(matches)} occurrences:")
for pos, match in matches:
    print(f"  Position {pos}: {match}")
    print(f"  Before: {repr(content[max(0,pos-50):pos])}")
    print(f"  After: {repr(content[pos:pos+150])}")
    print()
