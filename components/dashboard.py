import datetime
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from frontend.components.api_client import get_analytics_bundle, refresh_analytics

# Safe fragment decorator wrapper for compatibility across Streamlit versions (1.35.0+)
if hasattr(st, "fragment"):
    dashboard_fragment = st.fragment
else:
    dashboard_fragment = st.experimental_fragment

def _render_kpi_card(col, title, value):
    """Render a clean white KPI card styled with borders."""
    with col:
        st.markdown(f"""
        <div class="kpi-card" style="padding:15px; border:1px solid #E2E8F0; border-radius:12px; background:#fff; text-align:center;">
            <div class="kpi-title" style="font-size:0.9rem; color:#64748B; font-weight:600;">{title}</div>
            <div class="kpi-value" style="font-size:1.8rem; font-weight:800; color:#0F172A; margin-top:5px;">{value}</div>
        </div>
        """, unsafe_allow_html=True)

@dashboard_fragment
def render_dashboard_fragment() -> None:
    # ── Welcome Banner ────────────────────────────────────────────────────
    hour = datetime.datetime.now().hour
    greeting = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 18 else "Good Evening")

    st.markdown(f"""
    <div class="welcome-banner" style="background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%); padding:20px; border-radius:12px; margin-bottom:20px;">
        <h2 style="margin:0; color:#1E1B4B;">👋 {greeting}, HR</h2>
        <p style="margin:5px 0 0; color:#4338CA;">Here's what's happening with your recruitment pipelines today.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_dept, col_days, col_btn = st.columns([2, 2, 6])
    with col_dept:
        dept = st.selectbox("Department", ["All", "Engineering", "Analytics", "HR", "Sales", "Design"], label_visibility="collapsed")
    with col_days:
        days = st.selectbox("Timeframe", [7, 14, 30, 90], format_func=lambda x: f"Last {x} Days", index=2, label_visibility="collapsed")
    with col_btn:
        if st.button("🔄 Refresh Data"):
            refresh_analytics()
            st.rerun()

    # Fetch bundle
    bundle = get_analytics_bundle(department=dept, days=days)
    if not bundle:
        st.warning("Could not load analytics data. Ensure backend is running.")
        return

    # ── KPI Row ─────────────────────────────────────────────────────────
    ov = bundle.get("overview", {})
    kpi1 = st.columns(4)
    _render_kpi_card(kpi1[0], "Open Roles", ov.get("open_roles", 0))
    _render_kpi_card(kpi1[1], "Active Candidates", ov.get("active_candidates", 0))
    _render_kpi_card(kpi1[2], "Interviews This Week", ov.get("interviews_this_week", 0))
    _render_kpi_card(kpi1[3], "Avg Match Score", f"{ov.get('average_match_score', 0)}%")
    
    st.write("")
    
    # ── Charts Row 1 (Funnel & Trend) ───────────────────────────────────
    cc1, cc2 = st.columns(2)
    
    with cc1:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;'>Pipeline Funnel</h4>", unsafe_allow_html=True)
            funnel = bundle.get("funnel", {})
            f_keys = ["Applied", "Screened", "Interview", "Offer", "Hired"]
            fig1 = go.Figure(go.Funnel(
                y=f_keys,
                x=[funnel.get(k, 0) for k in f_keys],
                marker={"color": ["#94A3B8", "#64748B", "#475569", "#334155", "#0F172A"]}
            ))
            fig1.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250)
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})
            
    with cc2:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;'>Hiring Velocity</h4>", unsafe_allow_html=True)
            velocity = bundle.get("velocity", [])
            if velocity:
                df_v = pd.DataFrame(velocity)
                fig2 = px.line(df_v, x="date", y=["Applications", "Interviews", "Hires"],
                               color_discrete_sequence=["#94A3B8", "#4F46E5", "#10B981"])
                fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250, legend_title="")
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No velocity data.")

    st.write("")

    # ── Charts Row 2 (Interview Load & Source Quality) ─────────────────
    cc3, cc4 = st.columns(2)
    with cc3:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;'>Interview Load (Next 14 Days)</h4>", unsafe_allow_html=True)
            load = bundle.get("interview_load", [])
            if load:
                df_l = pd.DataFrame(load)
                fig3 = px.bar(df_l, x="date", y="count", color_discrete_sequence=["#6366F1"])
                fig3.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250)
                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No interviews scheduled in this window.")
                
    with cc4:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;'>Workforce Summary</h4>", unsafe_allow_html=True)
            wf = bundle.get("workforce", {})
            st.markdown(f"**Total Headcount:** {wf.get('headcount', 0)}")
            st.markdown(f"**Avg Performance:** {wf.get('avg_performance', 0)}")
            dept_counts = wf.get('by_department', {})
            if dept_counts:
                df_d = pd.DataFrame(list(dept_counts.items()), columns=["Department", "Count"])
                fig4 = px.pie(df_d, values="Count", names="Department", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig4.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=200)
                st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

def render_dashboard() -> None:
    render_dashboard_fragment()
