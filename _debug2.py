filepath = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\frontend\components\candidates.py"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the st.success line
for i, line in enumerate(lines):
    if "st.success" in line and "msg" in line:
        print(f"Line {i+1}: {repr(line)}")
        print(f"  Hex: {line.encode('utf-8').hex()}")
        # Show each character
        for j, ch in enumerate(line):
            print(f"  [{j}] U+{ord(ch):04X} {repr(ch)}")
