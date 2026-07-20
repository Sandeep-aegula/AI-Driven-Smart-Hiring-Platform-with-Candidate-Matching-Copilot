from pathlib import Path

path = Path(r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\frontend\components\reports.py")
text = path.read_text(encoding="utf-8")
start = text.index("def render_reports() -> None:")
end = text.index("def _trigger_export(report_type, fmt, payload):")
old_block = text[start:end]

new_block = """def render_reports() -> None:
    st.markdown(\"""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        📑 Reports & Export
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        Generate summaries and custom exports across all modules.
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    \""", unsafe_allow_html=True)
    t1, t2, t3, t4, t5 = st.tabs(["Recruitment Summary", "Job Reports", "Candidate Reports", "Employee Reports", "Custom Export"])
    with t1:
        st.markdown("**Recruitment Pipeline Summary**")
        dept_f = st.selectbox("Filter Department", ["All", "Engineering", "Analytics", "HR", "Sales", "Design"], key="rec_dept")
        summary = api_client.get_recruitment_summary(department=dept_f)
        if summary:
            funnel = summary.get("funnel", {})
            f_cols = st.columns(5)
            f_keys = ["Applied", "Screened", "Interview", "Offer", "Hired"]
            for i, k in enumerate(f_keys):
                f_cols[i].metric(k, funnel.get(k, 0))
            fig = go.Figure(go.Funnel(
                y=f_keys,
                x=[funnel.get(k, 0) for k in f_keys],
                marker={"color": ["#2563EB", "#06B6D4", "#F97316", "#9333EA", "#16A34A"]}
            ))
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=300)
            st.plotly_chart(fig, use_container_width=True)
            # Export
            st.markdown("<hr>", unsafe_allow_html=True)
            if st.button("Export Summary (PDF)", key="exp_sum_pdf"):
                _trigger_export("recruitment_summary", "pdf", funnel)
    with t2:
        st.markdown("**Per-Job Reports**")
        jobs = api_client.get_jobs()
        if jobs:
            job_opts = {j["id"]: j["title"] for j in jobs}
            job_id = st.selectbox("Select Job", options=list(job_opts.keys()), format_func=lambda x: job_opts[x], key="job_rep_sel")
            if st.button("Preview Job Report"):
                job_rep = api_client.get_job_report(job_id)
                _render_job_report(job_rep)
            st.markdown("<hr>", unsafe_allow_html=True)
            fmt = st.selectbox("Export Format", ["pdf", "xlsx", "csv"], key="job_rep_fmt")
            if st.button("Export Job Report", key="exp_job"):
                job_rep = api_client.get_job_report(job_id)
                _trigger_export(f"job_report_{job_id}", fmt, job_rep)
    with t3:
        st.markdown("**Candidate Reports**")
        cands = api_client.get_candidates()
        if cands:
            cand_opts = {c["id"]: c["name"] for c in cands}
            cand_id = st.selectbox("Select Candidate", options=list(cand_opts.keys()), format_func=lambda x: cand_opts[x], key="cand_rep_sel")
            if st.button("Preview Candidate Report"):
                cand_rep = api_client.get_candidate_report(cand_id)
                _render_candidate_report(cand_rep)
            fmt = st.selectbox("Export Format", ["pdf", "xlsx", "csv"], key="cand_rep_fmt")
            if st.button("Export Candidate Report", key="exp_cand"):
                cand_rep = api_client.get_candidate_report(cand_id)
                _trigger_export(f"candidate_report_{cand_id}", fmt, cand_rep)
    with t4:
        st.markdown("**Employee Reports**")
        emps = api_client.get_employees()
        if emps:
            emp_opts = {e["id"]: e["name"] for e in emps}
            emp_id = st.selectbox("Select Employee", options=list(emp_opts.keys()), format_func=lambda x: emp_opts[x], key="emp_rep_sel")
            if st.button("Preview Employee Report"):
                emp_rep = api_client.get_employee_report(emp_id)
                _render_employee_report(emp_rep)
            fmt = st.selectbox("Export Format", ["pdf", "xlsx", "csv"], key="emp_rep_fmt")
            if st.button("Export Employee Report", key="exp_emp"):
                emp_rep = api_client.get_employee_report(emp_id)
                _trigger_export(f"employee_report_{emp_id}", fmt, emp_rep)
    with t5:
        st.markdown("**Custom Export Builder**")
        entity = st.selectbox("Entity", ["jobs", "candidates", "interviews", "employees"])
        fmt = st.selectbox("Format", ["csv", "xlsx", "pdf"])
        # We could add dynamic field checklists here
        fields_str = st.text_input("Fields (comma-separated, leave blank for all)")
        if st.button("Generate Custom Export"):
            fields = [f.strip() for f in fields_str.split(",")] if fields_str else []
            data = api_client.generate_custom_report(entity, {}, fields, "")
            if data:
                _trigger_export(f"custom_export_{entity}", fmt, data)
"""

if old_block not in text:
    raise SystemExit("Old block not found")

path.write_text(text[:start] + new_block + text[end:], encoding="utf-8")
print("updated")
