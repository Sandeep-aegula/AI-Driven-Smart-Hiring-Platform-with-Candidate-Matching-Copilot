with open("frontend/views/ai_copilot.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

fixes = {
    157: "                append_message(\n",
    158: '                    "user",\n',
    159: '                    f"📎 Uploaded resume: **{uploaded_file.name}**\\n\\nPlease analyze this resume.",\n',
    160: "                )\n",
    161: "                st.rerun()\n",
}

for idx, new_line in fixes.items():
    lines[idx] = new_line

with open("frontend/views/ai_copilot.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Fixed indentation")
