import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
from datetime import datetime
from frontend.components import api_client

def _format_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d %B %Y")
    except Exception:
        return value

def _build_job_report_sections(job_rep: dict) -> dict:
    job = (job_rep or {}).get("job") or {}
    pipeline = (job_rep or {}).get("pipeline") or {}
    candidates = (job_rep or {}).get("candidates") or []

    required_skills = job.get("required_skills") or job.get("requirements") or []
    preferred_skills = job.get("preferred_skills") or job.get("nice_to_have_skills") or []

    summary_parts = []
    if job.get("title"):
        summary_parts.append(f"actively hiring for a {job['title']}")
    if job.get("department"):
        summary_parts.append(f"within the {job['department']} department")
    if required_skills:
        summary_parts.append(f"The role requires strong {', '.join(str(s) for s in required_skills[:3])} skills")
    if job.get("experience_min") or job.get("experience_max"):
        summary_parts.append(f"with {job.get('experience_min')}–{job.get('experience_max')} years of experience")
    if job.get("deadline"):
        summary_parts.append(f"Applications remain open until {_format_date(job.get('deadline'))}")

    return {
        "title": "Job Report",
        "basic_info": [
            ("Job Title", job.get("title")),
            ("Department", job.get("department")),
            ("Employment Type", job.get("employment_type")),
            ("Location", job.get("location")),
            ("Status", job.get("status")),
            ("Hiring Manager", job.get("hiring_manager")),
            ("Application Deadline", _format_date(job.get("deadline"))),
            ("Salary Range", f"₹{job.get('salary_min')} LPA – ₹{job.get('salary_max')} LPA" if job.get("salary_min") or job.get("salary_max") else None),
            ("Experience Required", f"{job.get('experience_min')}–{job.get('experience_max')} Years" if job.get("experience_min") or job.get("experience_max") else None),
        ],
        "description": job.get("description"),
        "responsibilities": job.get("responsibilities") or [],
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "pipeline": {
            "Total Candidates": pipeline.get("total_candidates", 0),
            "Qualified Candidates": pipeline.get("qualified", 0),
            "Interviews Scheduled": pipeline.get("interviews", 0),
            "Offers Released": pipeline.get("offers_released", 0),
            "Hired": pipeline.get("hired", 0),
        },
        "candidates": [
            {
                "name": c.get("name") or "Unknown",
                "match_score": c.get("match_score", "N/A"),
                "status": c.get("status", "Unknown"),
                "email": c.get("email") or "",
            }
            for c in candidates
        ],
        "hiring_summary": "This position is " + " ".join(summary_parts) + "." if summary_parts else None,
    }

def _render_job_report(job_rep: dict) -> None:
    sections = _build_job_report_sections(job_rep)
    if not sections:
        st.warning("No report data available.")
        return

    st.subheader(sections.get("title") or "Job Report")

    st.markdown("### Basic Information")
    basic_cols = st.columns(3)
    rendered = 0
    for label, value in sections.get("basic_info", []):
        if not value:
            continue
        col = basic_cols[rendered % 3]
        with col:
            st.markdown(f"**{label}**")
            st.markdown(str(value))
        rendered += 1

    description = sections.get("description")
    if description:
        st.markdown("### Job Description")
        st.markdown(description)

    responsibilities = sections.get("responsibilities") or []
    if responsibilities:
        st.markdown("### Key Responsibilities")
        for item in responsibilities:
            st.markdown(f"- {item}")

    required_skills = sections.get("required_skills") or []
    if required_skills:
        st.markdown("### Required Skills")
        st.markdown(", ".join(str(s) for s in required_skills))

    preferred_skills = sections.get("preferred_skills") or []
    if preferred_skills:
        st.markdown("### Preferred Skills")
        st.markdown(", ".join(str(s) for s in preferred_skills))

    st.markdown("### Candidate Statistics")
    stat_cols = st.columns(5)
    pipeline = sections.get("pipeline") or {}
    stat_cols[0].metric("Total Applicants", pipeline.get("Total Candidates", 0))
    stat_cols[1].metric("Qualified", pipeline.get("Qualified Candidates", 0))
    stat_cols[2].metric("Interviews", pipeline.get("Interviews Scheduled", 0))
    stat_cols[3].metric("Offers", pipeline.get("Offers Released", 0))
    stat_cols[4].metric("Hired", pipeline.get("Hired", 0))

    if sections.get("hiring_summary"):
        st.info(sections["hiring_summary"])

def render_reports() -> None:
    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        📑 Reports & Export
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        Generate summaries and custom exports across all modules.
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

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
                y=f_keys, x=[funnel.get(k, 0) for k in f_keys],
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
                st.json(cand_rep)
                
            st.markdown("<hr>", unsafe_allow_html=True)
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
                st.json(emp_rep)
                
            st.markdown("<hr>", unsafe_allow_html=True)
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

def _trigger_export(report_type, fmt, payload):
    with st.spinner(f"Generating {fmt.upper()} export..."):
        res = api_client.trigger_export(report_type, fmt, payload)
        if not res or "export_id" not in res:
            st.error("Failed to start export.")
            return
            
        export_id = res["export_id"]
        
        # Poll status
        for _ in range(30):
            status = api_client.check_export_status(export_id)
            if status == "completed":
                # Create a download button for the file
                st.success("Export ready!")
                url = f"{api_client.API_URL}/reports/export/{export_id}/download"
                st.markdown(f"[📥 Download File]({url})", unsafe_allow_html=True)
                break
            elif status == "failed":
                st.error("Export failed during generation.")
                break
            time.sleep(1.0)
        else:
            st.error("Export timed out.")
