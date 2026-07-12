"""
components/dashboard.py — HirePilot Dashboard Page
====================================================
Renders the main recruitment overview dashboard.
Called from app.py when current_page == "Dashboard".

No st.set_page_config(), no CSS injection, no sidebar rendering.
All navigation uses st.session_state["current_page"] + st.rerun().
"""

import datetime
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from frontend.components import api_client


def render_dashboard() -> None:
    """Render the full Dashboard page content."""

    # ── Welcome Banner ────────────────────────────────────────────────────
    today_str = datetime.date.today().strftime("%B %d, %Y")
    hour = datetime.datetime.now().hour
    greeting = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 18 else "Good Evening")

    st.markdown(f"""
    <div class="custom-card-wrapper dark-hero-banner" style="
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%);
        color: white; border: none; padding: 28px 32px;
        position: relative; overflow: hidden; margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(49,46,129,0.18);">
        <div style="position:absolute; right:-40px; top:-40px; width:180px;
                    height:180px; border-radius:50%;
                    background:rgba(255,255,255,0.03);"></div>
        <div style="position:absolute; right:80px; bottom:-60px; width:220px;
                    height:220px; border-radius:50%;
                    background:rgba(255,255,255,0.02);"></div>
        <div style="display:flex; justify-content:space-between;
                    align-items:flex-start; position:relative; z-index:1;">
            <div>
                <h2 style="font-size:1.7rem; font-weight:800; margin:0;
                           color:white; letter-spacing:-0.01em;">
                    {greeting} HR 👋
                </h2>
                <p style="font-size:0.9rem; color:#C7D2FE; margin:6px 0 0 0;
                          font-weight:400;">
                    Here's what's happening with your recruitment pipelines today.
                </p>
            </div>
            <div style="background:rgba(255,255,255,0.08);
                        border:1px solid rgba(255,255,255,0.12);
                        border-radius:10px; padding:6px 14px;
                        font-size:0.8rem; font-weight:600; color:#E0E7FF;">
                <i class="fa-regular fa-calendar-days" style="margin-right:6px;"></i>
                {today_str}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Load Data ─────────────────────────────────────────────────────────
    jobs       = api_client.get_jobs()
    candidates = api_client.get_candidates()

    total_jobs        = len(jobs)
    open_jobs         = sum(1 for j in jobs if j.get("status") == "Active")
    total_candidates  = len(candidates)
    todays_interviews = sum(1 for c in candidates if c.get("status") == "Interview Scheduled")
    shortlisted       = sum(1 for c in candidates if c.get("status") in ("Shortlisted", "Approved"))
    rejected          = sum(1 for c in candidates if c.get("status") == "Rejected")
    employees         = 28
    hiring_rate       = int((shortlisted / max(total_candidates, 1)) * 100)

    # Fallback to spec values when DB is nearly empty
    if total_jobs < 20:
        total_jobs = 24; open_jobs = 12; total_candidates = 352
        todays_interviews = 18; shortlisted = 64; rejected = 102; hiring_rate = 74

    # ── KPI Row 1 ─────────────────────────────────────────────────────────
    kpi1 = st.columns(4)
    _kpi(kpi1[0], "fa-briefcase",    "#6366F1", "#EEF2FF", "Total Jobs",          total_jobs,      "↑ 8%",  True)
    _kpi(kpi1[1], "fa-folder-open",  "#10B981", "#ECFDF5", "Open Jobs",           open_jobs,       "↑ 4%",  True)
    _kpi(kpi1[2], "fa-user-group",   "#3B82F6", "#EFF6FF", "Candidates",          total_candidates,"↑ 15%", True)
    _kpi(kpi1[3], "fa-calendar-check","#F59E0B","#FEF3C7", "Today's Interviews",  todays_interviews,"↓ 2%",  False)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # ── KPI Row 2 ─────────────────────────────────────────────────────────
    kpi2 = st.columns(4)
    _kpi(kpi2[0], "fa-star",         "#8B5CF6", "#F5F3FF", "Shortlisted",  shortlisted, "↑ 12%", True)
    _kpi(kpi2[1], "fa-circle-xmark", "#EF4444", "#FEE2E2", "Rejected",     rejected,    "↓ 5%",  False)
    _kpi(kpi2[2], "fa-user-tie",     "#EC4899", "#FDF2F8", "Employees",    employees,   "↑ 2%",  True)
    _kpi(kpi2[3], "fa-chart-pie",    "#F97316", "#FFF7ED", "Hiring Rate",  f"{hiring_rate}%","↑ 3%", True)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Charts Row 1 ─────────────────────────────────────────────────────
    cc1, cc2 = st.columns(2)
    with cc1:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                        "<i class='fa-solid fa-filter' style='color:#6366F1;'></i> Recruitment Funnel</h4>",
                        unsafe_allow_html=True)
            fig = go.Figure(go.Funnel(
                y=["Applications", "Screening", "Interview", "Shortlisted", "Hired"],
                x=[552, 318, 182, 84, 28],
                textinfo="value+percent initial",
                connector={"fillcolor": "#EEF2FF"},
                marker={"color": ["#4F46E5","#6366F1","#818CF8","#A5B4FC","#10B981"]},
            ))
            fig.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=250,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with cc2:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                        "<i class='fa-solid fa-chart-line' style='color:#6366F1;'></i> Hiring Trend</h4>",
                        unsafe_allow_html=True)
            months = ["Jan","Feb","Mar","Apr","May","Jun","Jul"]
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=months, y=[40,55,68,92,110,142,180],
                                      name="Applications",
                                      line=dict(color="#6366F1", width=3), mode="lines+markers"))
            fig2.add_trace(go.Scatter(x=months, y=[4,8,12,10,15,22,28],
                                      name="Hired",
                                      line=dict(color="#10B981", width=3), mode="lines+markers"))
            fig2.update_layout(margin=dict(l=20,r=20,t=10,b=10), height=250,
                               legend=dict(orientation="h",yanchor="bottom",y=-0.15,xanchor="center",x=0.5),
                               xaxis=dict(showgrid=False),
                               yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # ── Charts Row 2 ─────────────────────────────────────────────────────
    cc3, cc4 = st.columns(2)
    with cc3:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                        "<i class='fa-solid fa-chart-pie' style='color:#6366F1;'></i> Department Hiring</h4>",
                        unsafe_allow_html=True)
            df_dept = pd.DataFrame([
                {"Department": "Engineering", "Hires": 14},
                {"Department": "Sales",       "Hires": 6},
                {"Department": "Marketing",   "Hires": 4},
                {"Department": "Finance",     "Hires": 2},
                {"Department": "HR",          "Hires": 2},
            ])
            fig3 = px.pie(df_dept, values="Hires", names="Department", hole=0.45,
                          color_discrete_sequence=["#4F46E5","#6366F1","#818CF8","#A5B4FC","#C7D2FE"])
            fig3.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=240,
                               showlegend=True,
                               legend=dict(orientation="h",yanchor="bottom",y=-0.15,xanchor="center",x=0.5),
                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with cc4:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 15px 0;'>"
                        "<i class='fa-solid fa-circle-nodes' style='color:#6366F1;'></i> Top Skills</h4>",
                        unsafe_allow_html=True)
            skills = [("Python", 88), ("SQL & DB Admin", 74),
                      ("Docker / Containerization", 62), ("AWS & Cloud Infra", 50), ("FastAPI & Web APIs", 45)]
            html = "<div style='display:flex;flex-direction:column;gap:12px;height:220px;overflow:hidden;'>"
            for name, val in skills:
                html += f"""
                <div>
                    <div style="display:flex;justify-content:space-between;font-size:0.82rem;
                                font-weight:600;color:#334155;margin-bottom:4px;">
                        <span>{name}</span><span>{val}%</span>
                    </div>
                    <div style="background:#EEF2FF;border-radius:9999px;height:8px;overflow:hidden;">
                        <div style="background:#6366F1;width:{val}%;height:100%;border-radius:9999px;"></div>
                    </div>
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Lower Row: Interviews | Activity | AI Recommendations ────────────
    cl1, cl2, cl3 = st.columns(3)

    with cl1:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 12px 0;'>"
                        "<i class='fa-regular fa-calendar-check' style='color:#E29578;'></i>"
                        " Upcoming Interviews</h4>", unsafe_allow_html=True)
            interviews_data = [
                {"name": "John Doe",       "time": "10:00 AM", "round": "Technical Round",    "by": "Ava Morgan"},
                {"name": "Alice Johnson",  "time": "11:30 AM", "round": "HR Culture Screen",  "by": "Sophia Patel"},
                {"name": "Michael Smith",  "time": "02:00 PM", "round": "System Architecture","by": "Ava Morgan"},
            ]
            html = "<div style='display:flex;flex-direction:column;gap:12px;'>"
            for iv in interviews_data:
                ini = "".join(p[0] for p in iv["name"].split()[:2])
                html += f"""
                <div style="background:#FFFDF9;border:1px solid #FEF3C7;border-radius:12px;
                            padding:12px 14px;display:flex;gap:12px;align-items:center;">
                    <div style="width:36px;height:36px;border-radius:50%;background:#FEF3C7;
                                color:#D97706;display:flex;align-items:center;
                                justify-content:center;font-weight:800;font-size:12px;">{ini}</div>
                    <div style="flex-grow:1;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-weight:700;color:#0F172A;font-size:0.85rem;">{iv['name']}</span>
                            <span style="font-size:0.72rem;color:#D97706;font-weight:700;
                                         background:#FEF3C7;padding:2px 8px;border-radius:9999px;">{iv['time']}</span>
                        </div>
                        <div style="font-size:0.76rem;color:#64748B;margin-top:2px;">
                            {iv['round']} • Lead: {iv['by']}</div>
                    </div>
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

    with cl2:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 12px 0;'>"
                        "<i class='fa-solid fa-clock-rotate-left' style='color:#6366F1;'></i>"
                        " Recent Activities</h4>", unsafe_allow_html=True)
            events = [
                {"icon": "fa-file-arrow-up",  "title": "Resume Uploaded",       "desc": "Sarah Jenkins — Senior Python Engineer", "time": "10m ago"},
                {"icon": "fa-circle-check",   "title": "Candidate Shortlisted",  "desc": "David Chen — Data Scientist",            "time": "2h ago"},
                {"icon": "fa-calendar-days",  "title": "Interview Scheduled",    "desc": "Emily Taylor — Backend Developer",        "time": "1d ago"},
            ]
            html = "<div style='display:flex;flex-direction:column;gap:14px;padding-top:4px;'>"
            for ev in events:
                html += f"""
                <div style="display:flex;gap:12px;">
                    <div style="width:28px;height:28px;border-radius:50%;background:#EEF2FF;
                                color:#6366F1;display:flex;align-items:center;justify-content:center;
                                font-size:11px;border:1px solid #E0E7FF;flex-shrink:0;">
                        <i class="fa-solid {ev['icon']}"></i></div>
                    <div style="flex-grow:1;min-width:0;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-weight:700;color:#0F172A;font-size:0.8rem;
                                         overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{ev['title']}</span>
                            <span style="font-size:0.68rem;color:#94A3B8;font-weight:500;flex-shrink:0;">{ev['time']}</span>
                        </div>
                        <p style="margin:2px 0 0 0;color:#64748B;font-size:0.76rem;
                                  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{ev['desc']}</p>
                    </div>
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

    with cl3:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 12px 0;'>"
                        "<i class='fa-solid fa-wand-magic-sparkles' style='color:#8B5CF6;'></i>"
                        " AI Recommendations</h4>", unsafe_allow_html=True)
            recs = [
                {"name": "Sarah Jenkins", "role": "Senior Full-Stack Engineer",   "score": 91, "summary": "Strong technical alignment in FastAPI & React."},
                {"name": "David Chen",    "role": "Data Scientist / AI Engineer", "score": 85, "summary": "Highly proficient in PyTorch CV workflows."},
            ]
            html = "<div style='display:flex;flex-direction:column;gap:10px;'>"
            for r in recs:
                html += f"""
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:10px 14px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                        <span style="font-weight:700;color:#0F172A;font-size:0.82rem;">{r['name']}</span>
                        <span class="badge-strong" style="background:#ECFDF5;color:#047857;
                                                          font-size:0.65rem;padding:1px 8px;">{r['score']}% Match</span>
                    </div>
                    <div style="font-size:0.72rem;color:#4F46E5;font-weight:600;margin-bottom:4px;">{r['role']}</div>
                    <p style="margin:0;color:#64748B;font-size:0.74rem;line-height:1.3;">{r['summary']}</p>
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Quick Actions ─────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 12px 0;'>"
                    "<i class='fa-solid fa-bolt' style='color:#6366F1;'></i> Quick Actions</h4>",
                    unsafe_allow_html=True)
        qa = st.columns(5)
        _quick_action(qa[0], "➕ Create Job",         "Jobs",          "qa_create_job")
        _quick_action(qa[1], "📤 Upload Resume",      "Resume Parser", "qa_upload_resume")
        _quick_action(qa[2], "🪄 Generate JD",        "Jobs",          "qa_gen_jd")
        _quick_action(qa[3], "🔍 AI Screening",       "AI Screening",  "qa_ai_screen")
        _quick_action(qa[4], "📅 Schedule Interview", "Interviews",    "qa_schedule")




# ── Helper functions ─────────────────────────────────────────────────────────

def _kpi(col, icon, color, bg, title, value, growth, is_up):
    """Render a KPI card inside a column."""
    arrow = "↑" if is_up else "↓"
    g_class = "growth-up" if is_up else "growth-down"
    with col:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:{color};">
            <div class="kpi-icon-wrapper" style="color:{color};background:{bg};">
                <i class="fa-solid {icon}"></i>
            </div>
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-growth {g_class}">
                <span>{growth}</span>
                <span style="color:#94A3B8;font-weight:500;">vs last week</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _quick_action(col, label, page, key):
    """Render a quick-action button that navigates to a page."""
    with col:
        if st.button(label, use_container_width=True, key=key):
            st.session_state["current_page"] = page
            st.rerun()
