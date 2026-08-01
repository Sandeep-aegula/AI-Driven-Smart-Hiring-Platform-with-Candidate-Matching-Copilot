filepath = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\frontend\components\candidates.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()
idx = content.find('result.get("success")')
print(repr(content[idx-5:idx+300]))
