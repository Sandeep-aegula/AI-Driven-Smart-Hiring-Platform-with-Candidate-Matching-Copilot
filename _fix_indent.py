file_path = r'c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\frontend\components\candidates.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = 'c1, c2, c3, c4 = st.columns([2, 2, 2, 2])'
end_marker = 'st.warning("Please select a maximum of 4 candidates to compare.")'

start_idx = content.find(start_marker)
if start_idx < 0:
    print("ERROR: start_marker not found")
    exit(1)

end_idx = content.find(end_marker, start_idx)
if end_idx < 0:
    print("ERROR: end_marker not found")
    exit(1)

line_end = content.find('\n', end_idx)
if line_end < 0:
    line_end = len(content)

# Replacement with 1-space indentation for ALL nested lines (matching file style)
replacement = (
    'c1, c2, c3, c4 = st.columns([2, 2, 2, 2])\n'
    ' with c1:\n'
    '  if st.button("View Profile", type="primary", disabled=len(selected_rows) != 1, use_container_width=True):\n'
    '   st.session_state.selected_candidate_id = int(df.iloc[selected_rows[0]]["ID"])\n'
    '   st.rerun()\n'
    ' with c2:\n'
    '  if st.button("Compare Selected", disabled=len(selected_rows) < 2 or len(selected_rows) > 4, use_container_width=True):\n'
    '   if job_filter == 0:\n'
    '    st.error("Please select a specific Job Filter first to compare candidates.")\n'
    '   else:\n'
    '    st.session_state.compare_cands = [int(df.iloc[r]["ID"]) for r in selected_rows]\n'
    '    st.session_state.compare_job_id = job_filter\n'
    '    st.session_state.compare_mode = True\n'
    '    st.rerun()\n'
    ' with c3:\n'
    '  shortlist_disabled = len(selected_rows) == 0\n'
    '  shortlist_label = f"Shortlist Selected ({len(selected_rows)})" if selected_rows else "Shortlist Selected"\n'
    '  if st.button(shortlist_label, disabled=shortlist_disabled, use_container_width=True):\n'
    '   selected_app_ids = [int(df.iloc[r]["ID"]) for r in selected_rows]\n'
    '   with st.spinner(f"Shortlisting {len(selected_app_ids)} candidate(s)..."):\n'
    '    result = api_client.shortlist_bulk(selected_app_ids)\n'
    '    if result and result.get("success"):\n'
    '     msg = result.get("message", "Shortlist complete.")\n'
    '     st.success(f"✅ {msg}")\n'
    '     st.rerun()\n'
    '    else:\n'
    '     st.error("Failed to shortlist selected candidates.")\n'
    ' with c4:\n'
    '  if st.button("Clear Selection", use_container_width=True):\n'
    '   st.session_state.compare_cands = []\n'
    '   st.rerun()\n'
    'if len(selected_rows) > 4:\n'
    ' st.warning("Please select a maximum of 4 candidates to compare.")'
)

# The replacement still uses multi-level indent. Let me check the actual file style.
# From the repr: all inner lines use exactly 1 space.
# So we need: ' with c3:\n' '  shortlist_disabled...' NO - should be '  shortlist_disabled...' with 2 spaces?
# Wait, the repr showed '\n with c1:\n if st.button' - 1 space for with, 1 space for if.
# So EVERY line inside with/if blocks has exactly 1 space, regardless of nesting.

replacement_1space = (
    'c1, c2, c3, c4 = st.columns([2, 2, 2, 2])\n'
    ' with c1:\n'
    ' if st.button("View Profile", type="primary", disabled=len(selected_rows) != 1, use_container_width=True):\n'
    '  st.session_state.selected_candidate_id = int(df.iloc[selected_rows[0]]["ID"])\n'
    '  st.rerun()\n'
    ' with c2:\n'
    ' if st.button("Compare Selected", disabled=len(selected_rows) < 2 or len(selected_rows) > 4, use_container_width=True):\n'
    '  if job_filter == 0:\n'
    '   st.error("Please select a specific Job Filter first to compare candidates.")\n'
    '  else:\n'
    '   st.session_state.compare_cands = [int(df.iloc[r]["ID"]) for r in selected_rows]\n'
    '   st.session_state.compare_job_id = job_filter\n'
    '   st.session_state.compare_mode = True\n'
    '   st.rerun()\n'
    ' with c3:\n'
    '  shortlist_disabled = len(selected_rows) == 0\n'
    '  shortlist_label = f"Shortlist Selected ({len(selected_rows)})" if selected_rows else "Shortlist Selected"\n'
    '  if st.button(shortlist_label, disabled=shortlist_disabled, use_container_width=True):\n'
    '   selected_app_ids = [int(df.iloc[r]["ID"]) for r in selected_rows]\n'
    '   with st.spinner(f"Shortlisting {len(selected_app_ids)} candidate(s)..."):\n'
    '    result = api_client.shortlist_bulk(selected_app_ids)\n'
    '    if result and result.get("success"):\n'
    '     msg = result.get("message", "Shortlist complete.")\n'
    '     st.success(f"✅ {msg}")\n'
    '     st.rerun()\n'
    '    else:\n'
    '     st.error("Failed to shortlist selected candidates.")\n'
    ' with c4:\n'
    '  if st.button("Clear Selection", use_container_width=True):\n'
    '   st.session_state.compare_cands = []\n'
    '   st.rerun()\n'
    'if len(selected_rows) > 4:\n'
    ' st.warning("Please select a maximum of 4 candidates to compare.")'
)

new_content = content[:start_idx] + replacement_1space + content[line_end:]
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SUCCESS: File updated with 1-space indentation.")
# Verify syntax
import py_compile
try:
    py_compile.compile(file_path, doraise=True)
    print("Syntax check PASSED.")
except py_compile.PyCompileError as e:
    print(f"Syntax error: {e}")
