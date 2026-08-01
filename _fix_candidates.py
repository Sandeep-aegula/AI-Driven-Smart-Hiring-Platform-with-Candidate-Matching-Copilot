"""Fix shortlist button in candidates.py to use application_id."""
import re

filepath = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\frontend\components\candidates.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: Replace candidate ID with application ID in shortlist button
old1 = 'selected_app_ids = [int(df.iloc[r]["ID"]) for r in selected_rows]'
new1 = 'selected_app_ids = [int(df.iloc[r]["App ID"]) for r in selected_rows]'

if old1 in content:
    content = content.replace(old1, new1, 1)
    print("Fix 1: Replaced candidate ID with application ID in shortlist button")
else:
    print("Fix 1: Pattern not found -", repr(old1[:50]))

# Fix 2: Improve success/error handling for new response format
old2 = '''            if result and result.get("success"):
                msg = result.get("message", "Shortlist complete.")
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error("Failed to shortlist selected candidates.")'''

new2 = '''            if result and result.get("success"):
                updated = result.get("updated_count", 0)
                failed = result.get("failed_count", 0)
                if failed == 0:
                    st.success(f"✅ Shortlisted {updated} candidate(s) successfully.")
                else:
                    st.warning(f"⚠️ Shortlisted {updated} candidate(s); {failed} failed.")
                    for failure in result.get("failures", []):
                        app_id = failure.get("application_id", "?")
                        error = failure.get("error", "Unknown error")
                        st.error(f"Application {app_id}: {error}")
                st.rerun()
            else:
                st.error("Failed to shortlist selected candidates.")'''

if old2 in content:
    content = content.replace(old2, new2, 1)
    print("Fix 2: Updated shortlist success/error handling")
else:
    print("Fix 2: Pattern not found")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Done!")
