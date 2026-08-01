filepath = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\frontend\components\candidates.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Exact block from the file (1-space indentation)
old = ' if result and result.get("success"):\n msg = result.get("message", "Shortlist complete.")\n st.success(f"\u2705 {msg}")\n st.rerun()\n else:\n st.error("Failed to shortlist selected candidates.")'

new = ' if result and result.get("success"):\n updated = result.get("updated_count", 0)\n failed = result.get("failed_count", 0)\n if failed == 0:\n st.success(f"\u2705 Shortlisted {updated} candidate(s) successfully.")\n else:\n st.warning(f"\u26a0\ufe0f Shortlisted {updated} candidate(s); {failed} failed.")\n for failure in result.get("failures", []):\n app_id = failure.get("application_id", "?")\n error = failure.get("error", "Unknown error")\n st.error(f"Application {app_id}: {error}")\n st.rerun()\n else:\n st.error("Failed to shortlist selected candidates.")'

if old in content:
    content = content.replace(old, new, 1)
    print("SUCCESS: Replaced error handling block")
else:
    print("ERROR: Pattern not found")
    # Show what we're looking for
    idx = content.find('result.get("success")')
    if idx >= 0:
        print("Context:", repr(content[idx-5:idx+200]))

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
