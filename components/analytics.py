import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def apply_theme_layout(fig):
    """Utility chart theme style helper."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#475569", size=11),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    try:
        fig.update_xaxes(showgrid=True, gridcolor='#F1F5F9', zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor='#F1F5F9', zeroline=False)
    except Exception:
        pass
    return fig

def render_analytics():
    """Renders Section 8: Hiring Analytics charts grid."""
    st.markdown("<!-- SECTION 8: HIRING ANALYTICS -->", unsafe_allow_html=True)
    st.markdown("""
    <div class="custom-card-wrapper" style="margin-bottom: 24px;">
        <div class="section-title" style="margin-bottom: 0px; border-bottom: none; padding-bottom: 0px;">
            <span><i class="fa-solid fa-chart-line"></i></span> Hiring Analytics & Insights Dashboard
        </div>
    </div>
    """, unsafe_allow_html=True)

    cands = st.session_state.candidates_list
    total_cands = 1248 + (len(cands) - 5)
    shortlisted_cands = 412 + sum(1 for c in cands if c["status"] == "Shortlisted")
    interviews_cands = 85 + sum(1 for c in cands if c["status"] == "Interview Scheduled")
    offers_cands = 34 + sum(1 for c in cands if c["status"] == "Offer Released")

    c_row1_col1, c_row1_col2 = st.columns(2)
    c_row2_col1, c_row2_col2, c_row2_col3 = st.columns([4, 4, 3])

    # Chart 1: Applications by Month (Area)
    with c_row1_col1:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        applications = [150, 182, 224, 290, 312, 420 + (len(cands) - 5) * 5]
        
        fig_apps = px.area(
            x=months,
            y=applications,
            labels={"x": "Month", "y": "Applications Received"},
            title="<b>Application Submission Trends (H1 2026)</b>"
        )
        fig_apps.update_traces(
            line_color="#2563EB", 
            fillcolor="rgba(37, 99, 235, 0.08)",
            mode='lines+markers',
            marker=dict(size=6, line=dict(width=2, color='#FFFFFF'))
        )
        st.plotly_chart(apply_theme_layout(fig_apps), use_container_width=True)

    # Chart 2: Hiring Funnel
    with c_row1_col2:
        funnel_stages = ["Applied", "Screened", "Shortlisted", "Interviewed", "Offered"]
        funnel_vals = [total_cands, 820, shortlisted_cands, interviews_cands, offers_cands]
        
        fig_funnel = go.Figure(go.Funnel(
            y=funnel_stages,
            x=funnel_vals,
            textinfo="value+percent initial",
            connector_line_color="#CBD5E1",
            marker=dict(color=["#1E3A8A", "#2563EB", "#3B82F6", "#60A5FA", "#93C5FD"])
        ))
        fig_funnel.update_layout(title="<b>Active Recruitment Funnel Status</b>")
        st.plotly_chart(apply_theme_layout(fig_funnel), use_container_width=True)

    # Chart 3: Skill Distribution (Top Skills in candidate database)
    with c_row2_col1:
        skill_counts = {}
        for cand in cands:
            for skill in cand["skills"]:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:7]
        skill_y = [x[0] for x in sorted_skills]
        skill_x = [x[1] for x in sorted_skills]
        
        fig_skills = px.bar(
            x=skill_x,
            y=skill_y,
            orientation='h',
            title="<b>Frequent Candidate Skills (Top 7)</b>",
            labels={"x": "Occurrence Count", "y": "Skill Name"}
        )
        fig_skills.update_traces(
            marker_color="#2563EB",
            marker_line_color="#1D4ED8",
            marker_line_width=1,
            opacity=0.9
        )
        fig_skills.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(apply_theme_layout(fig_skills), use_container_width=True)

    # Chart 4: Department Hiring
    with c_row2_col2:
        depts = ["Engineering", "Data & AI", "Product Management", "Design", "Human Resources"]
        dept_hires = [24, 14, 8, 5, 3]
        
        fig_dept = px.pie(
            names=depts,
            values=dept_hires,
            title="<b>Hiring Placements by Department</b>",
            hole=0.45,
            color_discrete_sequence=["#1E3A8A", "#2563EB", "#3B82F6", "#60A5FA", "#93C5FD"]
        )
        fig_dept.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(apply_theme_layout(fig_dept), use_container_width=True)

    # Chart 5: Offer Acceptance Rate (Gauge Meter)
    with c_row2_col3:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=82,
            title={'text': "<b>Offer Acceptance Rate (%)</b>", 'font': {'size': 14, 'color': '#0F172A'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#475569"},
                'bar': {'color': "#2563EB"},
                'bgcolor': "#F1F5F9",
                'borderwidth': 1,
                'bordercolor': "#E2E8F0",
                'steps': [
                    {'range': [0, 60], 'color': '#FEE2E2'},
                    {'range': [60, 80], 'color': '#FEF3C7'},
                    {'range': [80, 100], 'color': '#D1FAE5'}
                ],
                'threshold': {
                    'line': {'color': "#EF4444", 'width': 3},
                    'thickness': 0.75,
                    'value': 85
                }
            }
        ))
        st.plotly_chart(apply_theme_layout(fig_gauge), use_container_width=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
