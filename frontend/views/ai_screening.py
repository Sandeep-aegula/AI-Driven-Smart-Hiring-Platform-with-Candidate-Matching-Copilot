import streamlit as st
import os
import sys
import plotly.graph_objects as go

# Setup path to import api_client
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.components import api_client
from frontend.components.page_utils import setup_page, render_sidebar_footer
from frontend.services.app_state import AppState
from frontend.services.cache import get_jobs_cached, get_candidates_cached

# Page Config
st.set_page_config(
    page_title="AI Screening - HirePilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

setup_page("AI Resume Screening", "AI-powered resume screening and analysis", page_key=__file__)

AppState.init()

# Load target openings and candidates (cached)
jobs_list = get_jobs_cached()
candidates_list = get_candidates_cached()

if not jobs_list or not candidates_list:
    st.warning("Please ensure you have at least one active job and candidate in your database before using AI Screening.")
else:
    # 1. Selection dropdown workflow
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        job_options = {f"{j['title']} ({j['department']})": j["id"] for j in jobs_list}
        selected_job_label = st.selectbox("Select Target Job Opening", list(job_options.keys()))
        job_id = job_options[selected_job_label]
        
    with col_sel2:
        candidate_options = {f"{c['name']} ({c.get('current_title', 'Applicant')})": c["id"] for c in candidates_list}
        
        # Preselect if candidate was selected in candidate tab
        preselect_idx = 0
        target_cand_id = st.session_state.get("selected_eval_cand_id")
        if target_cand_id:
            for idx, c in enumerate(candidates_list):
                if c["id"] == target_cand_id:
                    preselect_idx = idx
                    break
            # Clear state after reading
            st.session_state.selected_eval_cand_id = None

        selected_cand_label = st.selectbox(
            "Select Candidate to Evaluate",
            list(candidate_options.keys()),
            index=preselect_idx
        )
        candidate_id = candidate_options[selected_cand_label]

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # 2. Trigger Evaluation
    if st.button("🤖 Run AI Match Analysis", type="primary", width="stretch"):
        with st.spinner("Ollama qwen2.5-coder:7b is running evaluation... This may take up to 20 seconds..."):
            result = api_client.screen_candidate(candidate_id, job_id)
            if result:
                st.session_state[f"screening_res_{candidate_id}_{job_id}"] = result
                st.success("AI analysis completed successfully!")
            else:
                st.error("Ollama screening analysis failed to respond.")

    # 3. Render Match results
    result_key = f"screening_res_{candidate_id}_{job_id}"
    
    # Pre-load mock data fallback from parsed candidate profile details
    if result_key not in st.session_state:
        c_obj = next((c for c in candidates_list if c["id"] == candidate_id), {})
        if c_obj.get("match_score", 0) > 0:
            st.session_state[result_key] = {
                "overall_match_percent": c_obj.get("match_score", 75),
                "overall_recommendation": "Shortlist" if c_obj.get("match_score") >= 70 else "Reject",
                "resume_summary": c_obj.get("summary", ""),
                "explanation": "Loaded match score details based on parsed profile comparison.",
                "strengths": ["Strong coding alignment", "Experienced candidate profile", "Relevant technical degree"],
                "weaknesses": ["Minor gaps in specific cloud platforms"],
                "missing_skills": ["Kubernetes"],
                "radar": {"Skills": c_obj.get("match_score", 75), "Experience": c_obj.get("match_score", 75) - 5, "Education": 80, "Projects": 75}
            }

    if result_key in st.session_state:
        res = st.session_state[result_key]
        
        match_score = res.get("overall_match_percent", 0)
        rec = res.get("overall_recommendation", "Shortlist")
        rec_color = "#10B981" if rec == "Approve" else ("#F59E0B" if rec == "Shortlist" else "#EF4444")
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        # Bottom grid layout: overall circular match (indicator) + summary
        col_circular, col_summary = st.columns([1, 1])
        
        with col_circular:
            with st.container(border=True):
                st.markdown("<h4 style='font-size:1.05rem; font-weight:700; color:#0F172A; text-align:center;'>Overall Match Progress</h4>", unsafe_allow_html=True)
                
                # Plotly circular gauge chart
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=match_score,
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#475569"},
                        'bar': {'color': "#6366F1"},
                        'bgcolor': "#EEF2FF",
                        'borderwidth': 0,
                        'steps': [
                            {'range': [0, 60], 'color': '#FEE2E2'},
                            {'range': [60, 80], 'color': '#FEF3C7'},
                            {'range': [80, 100], 'color': '#ECFDF5'}
                        ],
                    },
                    number={'suffix': "%", 'font': {'size': 40, 'color': '#0F172A', 'weight': 'bold'}},
                ))
                fig_gauge.update_layout(
                    margin=dict(l=20, r=20, t=10, b=10),
                    height=160,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_gauge, width="stretch", config={'displayModeBar': False})
                
                st.markdown(f"<div style='text-align:center; font-weight:700; color:{rec_color}; font-size:1.1rem;'>Recommendation: {rec}</div>", unsafe_allow_html=True)

        with col_summary:
            with st.container(border=True):
                st.markdown("#### <i class='fa-solid fa-brain' style='color:#6366F1;'></i> AI Resume Summary", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size:0.88rem; color:#475569; line-height:1.4;'>{res.get('resume_summary')}</p>", unsafe_allow_html=True)
                
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                st.markdown("**Explanation Detail:**")
                st.write(res.get("explanation"))

        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        
        # Dimensions Split-pane: Radar Chart (left) & Progress Bars (right)
        col_radar, col_bars = st.columns([1, 1])
        
        radar_data = res.get("radar", {"Skills": 70, "Experience": 70, "Education": 70, "Projects": 70})
        
        with col_radar:
            with st.container(border=True):
                st.markdown("#### <i class='fa-solid fa-chart-pie' style='color:#6366F1;'></i> Match Polygon (Radar Chart)", unsafe_allow_html=True)
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=list(radar_data.values()),
                    theta=list(radar_data.keys()),
                    fill='toself',
                    fillcolor='rgba(99, 102, 241, 0.15)',
                    line=dict(color='#6366F1', width=2),
                    name='Candidate Details'
                ))
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 100]),
                        angularaxis=dict(gridcolor="#E2E8F0")
                    ),
                    showlegend=False,
                    margin=dict(l=30, r=30, t=20, b=20),
                    height=240,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_radar, width="stretch", config={'displayModeBar': False})

        with col_bars:
            with st.container(border=True):
                st.markdown("#### <i class='fa-solid fa-bars' style='color:#6366F1; margin-right:8px;'></i> Match Dimensions", unsafe_allow_html=True)
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                for dim_name, val in radar_data.items():
                    st.markdown(f"**{dim_name} Match** — {val}%")
                    st.progress(int(val) / 100)

        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

        # Strengths, Weaknesses, Missing Skills
        col_st, col_wk, col_ms = st.columns(3)
        with col_st:
            with st.container(border=True):
                st.markdown("##### <i class='fa-solid fa-circle-check' style='color:#10B981;'></i> Key Strengths", unsafe_allow_html=True)
                for item in res.get("strengths", []):
                    st.markdown(f"<span style='font-size:0.85rem; color:#334155;'>• {item}</span>", unsafe_allow_html=True)
        with col_wk:
            with st.container(border=True):
                st.markdown("##### <i class='fa-solid fa-triangle-exclamation' style='color:#F59E0B;'></i> Key Gaps", unsafe_allow_html=True)
                for item in res.get("weaknesses", []):
                    st.markdown(f"<span style='font-size:0.85rem; color:#334155;'>• {item}</span>", unsafe_allow_html=True)
        with col_ms:
            with st.container(border=True):
                st.markdown("##### <i class='fa-solid fa-circle-xmark' style='color:#EF4444;'></i> Missing Skills", unsafe_allow_html=True)
                for item in res.get("missing_skills", []):
                    st.markdown(f"<span style='font-size:0.85rem; color:#334155;'>• {item}</span>", unsafe_allow_html=True)

        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

        # Compare Candidate Panel
        with st.expander("📊 Compare Candidate details vs Job Requirements", expanded=True):
            job_details = api_client.get_job(job_id) or {}
            cand_details = api_client.get_candidate(candidate_id) or {}
            
            # Extract skills list
            job_skills = ", ".join(job_details.get("requirements", []))
            cand_skills = ", ".join([s.get("name") if isinstance(s, dict) else s for s in cand_details.get("skills", [])])
            
            st.markdown(f"""
            <table class="custom-table" style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem;">
                <thead>
                    <tr style="background-color: #F8FAFC; border-bottom: 2px solid #E2E8F0;">
                        <th style="padding: 10px; font-weight: 700; color: #475569; width: 25%;">Parameter</th>
                        <th style="padding: 10px; font-weight: 700; color: #475569; width: 37%;">Job Opening Requirements</th>
                        <th style="padding: 10px; font-weight: 700; color: #475569; width: 38%;">Candidate Profile Details</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 10px; font-weight: 700; color: #0F172A;">Job Title / Role</td>
                        <td style="padding: 10px; color: #475569;">{job_details.get('title')}</td>
                        <td style="padding: 10px; color: #0F172A; font-weight: 600;">{cand_details.get('current_title') or 'N/A'}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 10px; font-weight: 700; color: #0F172A;">Experience</td>
                        <td style="padding: 10px; color: #475569;">{job_details.get('experience_min')} - {job_details.get('experience_max')} Yrs</td>
                        <td style="padding: 10px; color: #0F172A; font-weight: 600;">{cand_details.get('years_experience')} Yrs</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 10px; font-weight: 700; color: #0F172A;">Skills</td>
                        <td style="padding: 10px; color: #475569;">{job_skills}</td>
                        <td style="padding: 10px; color: #0F172A; font-weight: 600;">{cand_skills}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 10px; font-weight: 700; color: #0F172A;">Location</td>
                        <td style="padding: 10px; color: #475569;">{job_details.get('location')}</td>
                        <td style="padding: 10px; color: #0F172A; font-weight: 600;">{cand_details.get('location')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 10px; font-weight: 700; color: #0F172A;">Employment Type</td>
                        <td style="padding: 10px; color: #475569;">{job_details.get('employment_type')}</td>
                        <td style="padding: 10px; color: #0F172A; font-weight: 600;">Full-time</td>
                    </tr>
                </tbody>
            </table>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

        # Bottom Decisions
        with st.container(border=True):
            st.markdown("#### Recruiters Decisions Dashboard")
            act_cols = st.columns(3)
            with act_cols[0]:
                if st.button("Shortlist Candidate", width="stretch", key="ai_short_btn"):
                    res = api_client.update_candidate_status(candidate_id, "Shortlisted")
                    if res:
                        st.toast("Candidate Shortlisted!", icon="✅")
                        st.rerun()
            with act_cols[1]:
                if st.button("Approve & Advance", type="primary", width="stretch", key="ai_appr_btn"):
                    res = api_client.update_candidate_status(candidate_id, "Approved")
                    if res:
                        st.toast("Candidate Approved!", icon="🎉")
                        st.rerun()
            with act_cols[2]:
                if st.button("Reject Candidate", width="stretch", key="ai_rej_btn"):
                    res = api_client.update_candidate_status(candidate_id, "Rejected")
                    if res:
                        st.toast("Candidate Rejected.", icon="❌")
                        st.rerun()
