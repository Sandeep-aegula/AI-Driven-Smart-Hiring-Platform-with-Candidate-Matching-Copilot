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

# The file uses exactly 1 space for ALL nested lines (every line inside with/if blocks)
replacement = '\n'.join([
    'c1, c2, c3, c4 = st.columns([2, 2, 2, 2])',
    ' with c1:',
    '  if st.button("View Profile", type="primary", disabled=len(selected_rows) != 1, use_container_width=True):',
    '   st.session_state.selected_candidate_id = int(df.iloc[selected_rows[0]]["ID"])',
    '   st.rerun()',
    ' with c2:',
    '  if st.button("Compare Selected", disabled=len(selected_rows) < 2 or len(selected_rows) > 4, use_container_width=True):',
    '   if job_filter == 0:',
    '    st.error("Please select a specific Job Filter first to compare candidates.")',
    '   else:',
    '    st.session_state.compare_cands = [int(df.iloc[r]["ID"]) for r in selected_rows]',
    '    st.session_state.compare_job_id = job_filter',
    '    st.session_state.compare_mode = True',
    '    st.rerun()',
    ' with c3:',
    '  shortlist_disabled = len(selected_rows) == 0',
    '  shortlist_label = f"Shortlist Selected ({len(selected_rows)})" if selected_rows else "Shortlist Selected"',
    '  if st.button(shortlist_label, disabled=shortlist_disabled, use_container_width=True):',
    '   selected_app_ids = [int(df.iloc[r]["ID"]) for r in selected_rows]',
    '   with st.spinner(f"Shortlisting {len(selected_app_ids)} candidate(s)..."):',
    '    result = api_client.shortlist_bulk(selected_app_ids)',
    '    if result and result.get("success"):',
    '     msg = result.get("message", "Shortlist complete.")',
    '     st.success(f"✅ {msg}")',
    '     st.rerun()',
    '    else:',
    '     st.error("Failed to shortlist selected candidates.")',
    ' with c4:',
    '  if st.button("Clear Selection", use_container_width=True):',
    '   st.session_state.compare_cands = []',
    '   st.rerun()',
    'if len(selected_rows) > 4:',
    ' st.warning("Please select a maximum of 4 candidates to compare.")',
])

new_content = content[:start_idx] + replacement + content[line_end:]
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SUCCESS: File updated.")
# Verify syntax
import py_compile
try:
    py_compile.compile(file_path, doraise=True)
    print("Syntax check PASSED.")
except py_compile.PyCompileError as e:
    print(f"Syntax error: {e}")
