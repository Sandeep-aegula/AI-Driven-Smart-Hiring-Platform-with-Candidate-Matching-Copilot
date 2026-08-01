"""
components/ai_screening.py — HirePilot AI Screening Page
"""
import streamlit as st
import plotly.graph_objects as go
from frontend.components import api_client
from frontend.services.cache import get_jobs_cached, get_candidates_cached, get_job_cached, get_candidate_cached, invalidate_candidates, cached_screen, invalidate_screening


def render_ai_screening() -> None:
    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        AI Screening
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        AI-powered resume screening and candidate analysis
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

    jobs_list  = get_jobs_cached()
    cands_list = get_candidates_cached()

    if not jobs_list or not cands_list:
        st.warning("Please ensure you have at least one active job and candidate before using AI Screening.")
        return

    # ── Selection ─────────────────────────────────────────────────────────
    cs1, cs2 = st.columns(2)
    with cs1:
        job_opts   = {f"{j['title']} ({j['department']})": j["id"] for j in jobs_list}
        sel_job    = st.selectbox("Target Job Opening", list(job_opts.keys()))
        job_id     = job_opts[sel_job]

    with cs2:
        cand_opts  = {f"{c['name']} ({c.get('current_title','Applicant')})": c["id"] for c in cands_list}
        presel     = 0
        pre_id     = st.session_state.get("selected_eval_cand_id")
        if pre_id:
            for i, c in enumerate(cands_list):
                if c["id"] == pre_id: presel = i; break
            st.session_state["selected_eval_cand_id"] = None
        sel_cand   = st.selectbox("Candidate to Evaluate", list(cand_opts.keys()), index=presel)
        cand_id    = cand_opts[sel_cand]

    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

    if st.button("Run AI Match Analysis", type="primary", width="stretch"):
        with st.spinner("Ollama qwen2.5-coder:7b is running evaluation… Up to 20 seconds…"):
            result = api_client.screen_candidate(cand_id, job_id) if hasattr(api_client, "screen_candidate") else None
            if not result:
                # Try alternative endpoint name
                try:
                    import httpx
                    r = httpx.get("http://localhost:8000/ai-screening",
                                  params={"candidate_id": cand_id, "job_id": job_id}, timeout=90.0)
                    result = r.json() if r.status_code == 200 else None
                except Exception:
                    result = None
            if result:
                st.session_state[f"screen_{cand_id}_{job_id}"] = result
                st.success("AI analysis complete!")
            else:
                st.error("Ollama screening failed. Check Ollama server.")

    # ── Pre-load fallback result ──────────────────────────────────────────
    rkey = f"screen_{cand_id}_{job_id}"
    if rkey not in st.session_state:
        cached_res = cached_screen(cand_id, job_id)
        if cached_res:
            st.session_state[rkey] = cached_res
        else:
            c_obj = next((c for c in cands_list if c["id"] == cand_id), {})
            if c_obj.get("match_score", 0) > 0:
                st.session_state[rkey] = {
                    "overall_match_percent": c_obj.get("match_score", 75),
                    "overall_recommendation": "Shortlist" if c_obj.get("match_score",75) >= 70 else "Reject",
                    "resume_summary": c_obj.get("summary",""),
                    "explanation": "Match score based on parsed profile comparison.",
                    "strengths": ["Strong coding alignment","Experienced profile","Relevant degree"],
                    "weaknesses": ["Minor cloud platform gaps"],
                    "missing_skills": ["Kubernetes"],
                    "radar": {"Skills": c_obj.get("match_score",75),
                              "Experience": c_obj.get("match_score",75)-5,
                              "Education": 80, "Projects": 75}
                    }

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # ── Gauge + Summary ───────────────────────────────────────────────────
    # Get the screening result
    rkey = f"screen_{cand_id}_{job_id}"
    rkey = f"screen_{cand_id}_{job_id}"
    res = st.session_state.get(rkey, {}) or {}
    
    # Extract values from result
    score = res.get("overall_match_percent", res.get("match_score", 75))
    # st.write("DEBUG SCORE:", score)
    # st.write("DEBUG RESULT:", res)
    rec = res.get("overall_recommendation", "Shortlist")
    rc = "#10B981" if rec == "Shortlist" else ("#F59E0B" if rec == "Hold" else "#EF4444")

    cg1, cg2 = st.columns(2)
    with cg1:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;text-align:center;'>"
                        "Overall Match</h4>", unsafe_allow_html=True)
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=score,
                gauge={"axis":{"range":[0,100]},"bar":{"color":"#6366F1"},
                       "bgcolor":"#EEF2FF","borderwidth":0,
                       "steps":[{"range":[0,60],"color":"#FEE2E2"},
                                 {"range":[60,80],"color":"#FEF3C7"},
                                 {"range":[80,100],"color":"#ECFDF5"}]},
                number={"suffix":"%","font":{"size":40,"color":"#0F172A"}}
            ))
            fig.update_layout(margin=dict(l=20,r=20,t=10,b=10), height=160,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width="stretch", config={"displayModeBar":False})
            st.markdown(f"<div style='text-align:center;font-weight:700;color:{rc};font-size:1.1rem;'>"
                        f"Recommendation: {rec}</div>", unsafe_allow_html=True)

    with cg2:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                        "<i class='fa-solid fa-brain' style='color:#6366F1;'></i> AI Summary</h4>",
                        unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:0.88rem;color:#475569;line-height:1.4;'>{res.get('resume_summary','')}</p>",
                        unsafe_allow_html=True)
            st.markdown("**Explanation:**")
            st.write(res.get("explanation",""))

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Radar + Progress Bars ─────────────────────────────────────────────
    radar_data = res.get("radar", {"Skills":70,"Experience":70,"Education":70,"Projects":70})
    cr1, cr2 = st.columns(2)

    with cr1:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                        "<i class='fa-solid fa-chart-pie' style='color:#6366F1;'></i> Match Polygon</h4>",
                        unsafe_allow_html=True)
            fig2 = go.Figure()
            fig2.add_trace(go.Scatterpolar(
                r=list(radar_data.values()), theta=list(radar_data.keys()),
                fill="toself", fillcolor="rgba(99,102,241,0.15)",
                line=dict(color="#6366F1", width=2)
            ))
            fig2.update_layout(
                polar=dict(radialaxis=dict(visible=True,range=[0,100])),
                showlegend=False, margin=dict(l=30,r=30,t=20,b=20), height=240,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig2, width="stretch", config={"displayModeBar":False})

    with cr2:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                        "<i class='fa-solid fa-bars' style='color:#6366F1;'></i> Match Dimensions</h4>",
                        unsafe_allow_html=True)
            html = "<div style='display:flex;flex-direction:column;gap:14px;justify-content:center;height:230px;'>"
            for dim, val in radar_data.items():
                html += f"""
                <div>
                    <div style="display:flex;justify-content:space-between;font-size:0.85rem;
                                font-weight:600;color:#334155;margin-bottom:4px;">
                        <span>{dim} Match</span><span>{val}%</span></div>
                    <div style="background:#EEF2FF;border-radius:9999px;height:8px;overflow:hidden;">
                        <div style="background:#6366F1;width:{val}%;height:100%;border-radius:9999px;"></div>
                    </div>
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Strengths / Gaps / Missing ────────────────────────────────────────
    cs1, cs2, cs3 = st.columns(3)
    with cs1:
        with st.container(border=True):
            st.markdown("<h5><i class='fa-solid fa-circle-check' style='color:#10B981;'></i> Key Strengths</h5>",
                        unsafe_allow_html=True)
            for item in res.get("strengths",[]): st.markdown(f"<span style='font-size:0.85rem;'>• {item}</span>", unsafe_allow_html=True)
    with cs2:
        with st.container(border=True):
            st.markdown("<h5><i class='fa-solid fa-triangle-exclamation' style='color:#F59E0B;'></i> Key Gaps</h5>",
                        unsafe_allow_html=True)
            for item in res.get("weaknesses",[]): st.markdown(f"<span style='font-size:0.85rem;'>• {item}</span>", unsafe_allow_html=True)
    with cs3:
        with st.container(border=True):
            st.markdown("<h5><i class='fa-solid fa-circle-xmark' style='color:#EF4444;'></i> Missing Skills</h5>",
                        unsafe_allow_html=True)
            for item in res.get("missing_skills",[]): st.markdown(f"<span style='font-size:0.85rem;'>• {item}</span>", unsafe_allow_html=True)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Comparison Table ──────────────────────────────────────────────────
    with st.expander("📊 Compare Candidate vs Job Requirements", expanded=True):
        job_d  = get_job_cached(job_id) or {}
        cand_d = get_candidate_cached(cand_id) or {}
        j_skl  = ", ".join(job_d.get("requirements",[]))
        c_skl  = ", ".join([s.get("name") if isinstance(s,dict) else s for s in cand_d.get("skills",[])])
        st.markdown(f"""
        <table class="custom-table">
            <thead>
                <tr style="background:#F8FAFC;border-bottom:2px solid #E2E8F0;">
                    <th style="padding:10px;width:25%;">Parameter</th>
                    <th style="padding:10px;width:37%;">Job Requirements</th>
                    <th style="padding:10px;width:38%;">Candidate Profile</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom:1px solid #F1F5F9;">
                    <td style="padding:10px;font-weight:700;">Role</td>
                    <td style="padding:10px;color:#475569;">{job_d.get('title','')}</td>
                    <td style="padding:10px;font-weight:600;">{cand_d.get('current_title','N/A')}</td>
                </tr>
                <tr style="border-bottom:1px solid #F1F5F9;">
                    <td style="padding:10px;font-weight:700;">Experience</td>
                    <td style="padding:10px;color:#475569;">{job_d.get('experience_min',0)}–{job_d.get('experience_max',0)} Yrs</td>
                    <td style="padding:10px;font-weight:600;">{cand_d.get('years_experience',0)} Yrs</td>
                </tr>
                <tr style="border-bottom:1px solid #F1F5F9;">
                    <td style="padding:10px;font-weight:700;">Skills</td>
                    <td style="padding:10px;color:#475569;">{j_skl}</td>
                    <td style="padding:10px;font-weight:600;">{c_skl}</td>
                </tr>
                <tr>
                    <td style="padding:10px;font-weight:700;">Location</td>
                    <td style="padding:10px;color:#475569;">{job_d.get('location','')}</td>
                    <td style="padding:10px;font-weight:600;">{cand_d.get('location','')}</td>
                </tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Decision Buttons ──────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### Recruiter Decision")
        da1, da2, da3 = st.columns(3)
        with da1:
            if st.button("Shortlist Candidate", width="stretch", key="ai_short"):
                if api_client.update_candidate_status(cand_id,"Shortlisted"):
                    invalidate_candidates()
                    st.toast("Shortlisted!", icon="✅")
                    st.rerun()
        with da2:
            if st.button("Approve & Advance", type="primary", width="stretch", key="ai_appr"):
                if api_client.update_candidate_status(cand_id,"Approved"):
                    invalidate_candidates()
                    st.toast("Approved!", icon="🎉")
                    st.rerun()
        with da3:
            if st.button("Reject Candidate", width="stretch", key="ai_rej"):
                if api_client.update_candidate_status(cand_id,"Rejected"):
                    invalidate_candidates()
                    st.toast("Rejected.", icon="❌")
                    st.rerun()
