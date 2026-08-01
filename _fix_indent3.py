file_path = r'c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\frontend\components\candidates.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Show exact indentation of the existing code
start_idx = content.find('c1, c2, c3 = st.columns([2, 2, 6])')
if start_idx < 0:
    start_idx = content.find('c1, c2, c3, c4 = st.columns([2, 2, 2, 2])')

print("Existing code indentation pattern:")
lines = content[start_idx:start_idx+800].split('\n')
for i, line in enumerate(lines[:30]):
    if line.strip():
        spaces = len(line) - len(line.lstrip())
        print(f"  Line {i}: {spaces} spaces | {line[:60]}")
