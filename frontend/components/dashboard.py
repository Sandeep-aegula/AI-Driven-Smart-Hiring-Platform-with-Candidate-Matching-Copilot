import datetime
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

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

def _get_funnel_data(bundle):
    """Extract and process funnel data from bundle, with fallback to demo data."""
    funnel = bundle.get("funnel", {})
    
    # Check if we have real data
    has_real_data = any(funnel.get(k, 0) > 0 for k in ["Applied", "Screened", "Interview", "Offer", "Hired"])
    
    if has_real_data:
        # Use real data from backend
        stages = [
            ("Applied", funnel.get("Applied", 0)),
            ("Resume Screened", funnel.get("Screened", 0)),
            ("Shortlisted", max(funnel.get("Screened", 0) - funnel.get("Interview", 0), 0)),
            ("Technical Interview", funnel.get("Interview", 0)),
            ("HR Interview", max(funnel.get("Interview", 0) - funnel.get("Offer", 0), 0)),
            ("Final Interview", max(funnel.get("Interview", 0) - funnel.get("Offer", 0), 0)),
            ("Offer Extended", funnel.get("Offer", 0)),
            ("Offer Accepted", max(funnel.get("Offer", 0) - funnel.get("Hired", 0), 0)),
            ("Hired", funnel.get("Hired", 0)),
        ]
    else:
        # Realistic demo data
        stages = [
            ("Applied", 240),
            ("Resume Screened", 180),
            ("Shortlisted", 120),
            ("Technical Interview", 80),
            ("HR Interview", 52),
            ("Final Interview", 34),
            ("Offer Extended", 18),
            ("Offer Accepted", 12),
            ("Hired", 10),
        ]
    
    return stages

def _calculate_funnel_metrics(stages):
    """Calculate conversion rates, drop-offs, and KPIs from funnel stages."""
    if not stages:
        return {}
    
    counts = [count for _, count in stages]
    names = [name for name, _ in stages]
    
    # Calculate conversion rates (from previous stage)
    conversion_rates = [100.0]  # First stage is 100%
    drop_off_rates = [0.0]
    
    for i in range(1, len(counts)):
        if counts[i-1] > 0:
            conv = (counts[i] / counts[i-1]) * 100
            drop = 100 - conv
        else:
            conv = 0
            drop = 100
        conversion_rates.append(round(conv, 1))
        drop_off_rates.append(round(drop, 1))
    
    # Overall metrics
    total_applicants = counts[0]
    hired = counts[-1]
    overall_conversion = round((hired / total_applicants * 100), 1) if total_applicants > 0 else 0
    overall_drop_off = round(100 - overall_conversion, 1)
    
    # Find biggest drop-off
    max_drop_idx = np.argmax(drop_off_rates[1:]) + 1 if len(drop_off_rates) > 1 else 0
    biggest_drop_stage = names[max_drop_idx] if max_drop_idx < len(names) else "N/A"
    biggest_drop_value = drop_off_rates[max_drop_idx]
    
    # Highest conversion (excluding first stage)
    max_conv_idx = np.argmax(conversion_rates[1:]) + 1 if len(conversion_rates) > 1 else 0
    highest_conv_stage = names[max_conv_idx] if max_conv_idx < len(names) else "N/A"
    highest_conv_value = conversion_rates[max_conv_idx]
    
    # Current active stage (first stage with count > 0 after first)
    active_stage = "Applied"
    for i in range(1, len(counts)):
        if counts[i] > 0:
            active_stage = names[i]
            break
    
    return {
        "stages": stages,
        "names": names,
        "counts": counts,
        "conversion_rates": conversion_rates,
        "drop_off_rates": drop_off_rates,
        "total_applicants": total_applicants,
        "hired": hired,
        "overall_conversion": overall_conversion,
        "overall_drop_off": overall_drop_off,
        "biggest_drop_stage": biggest_drop_stage,
        "biggest_drop_value": biggest_drop_value,
        "highest_conv_stage": highest_conv_stage,
        "highest_conv_value": highest_conv_value,
        "active_stage": active_stage,
        "hiring_success_rate": overall_conversion,
    }

def _render_funnel_kpis(metrics):
    """Render KPI summary cards above the funnel."""
    kpi_cols = st.columns(5)
    
    kpis = [
        ("Total Applicants", f"{metrics['total_applicants']:,}"),
        ("Conversion Rate", f"{metrics['overall_conversion']}%"),
        ("Hiring Rate", f"{metrics['hiring_success_rate']}%"),
        ("Drop-off Rate", f"{metrics['overall_drop_off']}%"),
        ("Avg Time to Hire", "24 days"),  # Could be calculated from velocity data
    ]
    
    for i, (title, value) in enumerate(kpis):
        with kpi_cols[i]:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px; text-align:center;">
                <div style="font-size:0.8rem; color:#64748B; font-weight:600; margin-bottom:4px;">{title}</div>
                <div style="font-size:1.5rem; font-weight:800; color:#0F172A;">{value}</div>
            </div>
            """, unsafe_allow_html=True)

def _render_funnel_chart(metrics):
    """Render the professional Plotly funnel chart."""
    names = metrics["names"]
    counts = metrics["counts"]
    conversion_rates = metrics["conversion_rates"]
    drop_off_rates = metrics["drop_off_rates"]
    
    # Create custom hover text
    hover_text = []
    for i in range(len(names)):
        hover_text.append(
            f"<b>{names[i]}</b><br>"
            f"Candidates: {counts[i]:,}<br>"
            f"Conversion: {conversion_rates[i]}%<br>"
            f"Drop-off: {drop_off_rates[i]}%"
        )
    
    # Professional color scheme
    colors = [
        "#4F46E5",  # Applied - Indigo
        "#6366F1",  # Resume Screened - Indigo lighter
        "#818CF8",  # Shortlisted - Blue
        "#A5B4FC",  # Technical Interview - Blue lighter
        "#C7D2FE",  # HR Interview - Blue lightest
        "#DBEAFE",  # Final Interview - Blue very light
        "#BFDBFE",  # Offer Extended - Blue
        "#93C5FD",  # Offer Accepted - Blue
        "#10B981",  # Hired - Emerald
    ]
    
    fig = go.Figure(go.Funnel(
        y=names,
        x=counts,
        textinfo="value+percent initial",
        textposition="inside",
        textfont=dict(size=12, color="white", family="Inter"),
        marker=dict(
            color=colors,
            line=dict(width=1, color="rgba(255,255,255,0.3)")
        ),
        connector=dict(
            line=dict(color="#E2E8F0", width=2, dash="solid"),
            fillcolor="rgba(226, 232, 240, 0.5)"
        ),
        hoverinfo="text",
        hovertext=hover_text,
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Inter",
            bordercolor="#E2E8F0"
        ),
        opacity=0.95
    ))
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#1E293B"),
        funnelmode="stack",
        funnelgap=0.15,
    )
    
    return fig

def _render_additional_analytics(metrics):
    """Render additional analytics below the funnel."""
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    
    # Analytics cards
    col1, col2, col3, col4 = st.columns(4)
    
    analytics = [
        ("Biggest Drop-off", f"{metrics['biggest_drop_stage']}", f"{metrics['biggest_drop_value']}% drop", "#EF4444"),
        ("Highest Conversion", f"{metrics['highest_conv_stage']}", f"{metrics['highest_conv_value']}% conversion", "#10B981"),
        ("Active Stage", f"{metrics['active_stage']}", "Currently processing", "#3B82F6"),
        ("Hiring Success Rate", f"{metrics['hiring_success_rate']}%", "Overall pipeline health", "#8B5CF6"),
    ]
    
    for i, (title, value, subtitle, color) in enumerate(analytics):
        with [col1, col2, col3, col4][i]:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px; text-align:center; border-left:4px solid {color};">
                <div style="font-size:0.75rem; color:#64748B; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px;">{title}</div>
                <div style="font-size:1.25rem; font-weight:800; color:#0F172A; margin-bottom:4px;">{value}</div>
                <div style="font-size:0.75rem; color:#64748B;">{subtitle}</div>
            </div>
            """, unsafe_allow_html=True)

@dashboard_fragment
def render_dashboard_fragment() -> None:
    # ── Welcome Banner ────────────────────────────────────────────────────
    hour = datetime.datetime.now().hour
    # greeting = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 18 else "Good Evening")
    greeting = "Hi Hiring Team"

    st.markdown(f"""
    <div class="welcome-banner" style="background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%); padding:20px; border-radius:12px; margin-bottom:20px;">
        <h2 style="margin:0; color:#1E1B4B;">👋 {greeting}</h2>
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
            st.plotly_chart(fig1, width="stretch", config={"displayModeBar": False})
            
    with cc2:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;'>Hiring Velocity</h4>", unsafe_allow_html=True)
            velocity = bundle.get("velocity", [])
            if velocity:
                df_v = pd.DataFrame(velocity)
                fig2 = px.line(df_v, x="date", y=["Applications", "Interviews", "Hires"],
                               color_discrete_sequence=["#94A3B8", "#4F46E5", "#10B981"])
                fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250, legend_title="")
                st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})
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
                st.plotly_chart(fig3, width="stretch", config={"displayModeBar": False})
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
                st.plotly_chart(fig4, width="stretch", config={"displayModeBar": False})

def render_dashboard() -> None:
    render_dashboard_fragment()
