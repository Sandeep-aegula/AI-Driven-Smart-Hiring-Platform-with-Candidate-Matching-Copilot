filepath = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\backend\api\routes\candidates.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add json import
if "import json" not in content:
    content = content.replace("from __future__ import annotations", "from __future__ import annotations\nimport json")
    print("Added import json")

# Add Response to fastapi imports
if "from fastapi import APIRouter, HTTPException, Response" not in content:
    content = content.replace(
        "from fastapi import APIRouter, HTTPException",
        "from fastapi import APIRouter, HTTPException, Response"
    )
    print("Added Response to fastapi imports")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Done!")
