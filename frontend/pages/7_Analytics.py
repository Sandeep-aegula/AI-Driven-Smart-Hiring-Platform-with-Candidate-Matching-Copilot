import streamlit as st
import os
import sys
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from frontend.components.page_utils import setup_page, render_sidebar_footer
from frontend.services.json_storage import get_dashboard_stats
from frontend.services.app_state import AppState

# Page Config
st.set_page_config(
    page_title="Analytics - HirePilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

setup_page("Analytics Dashboard", "Interactive recruitment statistics and reporting", page_key=__file__)

# KPI row
kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.markdown("""
    <div class="kpi-card" style="border-left-color: #6366F1;">
        <div class="kpi-icon-wrapper" style="color: #6366F1; background-color: #EEF2FF;"><i class="fa-solid fa-folder-open"></i></div>
        <div class="kpi-title">Total Applications</div>
        <div class="kpi-value">352</div>
        <div class="kpi-growth growth-up"><span>↑ 12%</span> <span style="color: #94A3B8; font-weight: 500;">vs last month</span></div>
    </div>
    """, unsafe_allow_html=True)
with kpi_cols[1]:
    st.markdown("""
    <div class="kpi-card" style="border-left-color: #F59E0B;">
        <div class="kpi-icon-wrapper" style="color: #F59E0B; background-color: #FEF3C7;"><i class="fa-solid fa-calendar-days"></i></div>
        <div class="kpi-title">Interviewed</div>
        <div class="kpi-value">92</div>
        <div class="kpi-growth growth-up"><span>↑ 8%</span> <span style="color: #94A3B8; font-weight: 500;">vs last month</span></div>
    </div>
    """, unsafe_allow_html=True)
with kpi_cols[2]:
    st.markdown("""
    <div class="kpi-card" style="border-left-color: #8B5CF6;">
        <div class="kpi-icon-wrapper" style="color: #8B5CF6; background-color: #F5F3FF;"><i class="fa-solid fa-star"></i></div>
        <div class="kpi-title">Shortlisted</div>
        <div class="kpi-value">64</div>
        <div class="kpi-growth growth-up"><span>↑ 4%</span> <span style="color: #94A3B8; font-weight: 500;">vs last month</span></div>
    </div>
    """, unsafe_allow_html=True)
with kpi_cols[3]:
    st.markdown("""
    <div class="kpi-card" style="border-left-color: #10B981;">
        <div class="kpi-icon-wrapper" style="color: #10B981; background-color: #ECFDF5;"><i class="fa-solid fa-circle-check"></i></div>
        <div class="kpi-title">Hired</div>
        <div class="kpi-value">28</div>
        <div class="kpi-growth growth-up"><span>↑ 18%</span> <span style="color: #94A3B8; font-weight: 500;">vs last month</span></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Tabs
tab_funnel, tab_trends, tab_talent, tab_recruiters = st.tabs([
    "📊 Pipeline & Funnel", "📈 Trends & Departments", "⚡ Talent & Channels", "💼 Recruiter Analytics"
])

with tab_funnel:
    col_t1_left, col_t1_right = st.columns(2)
    
    with col_t1_left:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 1.05rem; font-weight: 700; color: #0F172A; margin-bottom: 10px;'>Hiring Funnel Conversion</h4>", unsafe_allow_html=True)
            # Funnel Chart
            funnel_stages = ["Applied", "Screened", "Interviewed", "Shortlisted", "Hired"]
            funnel_vals = [352, 210, 92, 64, 28]
            fig_fun = go.Figure(go.Funnel(
                y=funnel_stages, x=funnel_vals,
                textinfo="value+percent initial",
                connector={"fillcolor": "#EEF2FF"},
                marker={"color": ["#4F46E5", "#6366F1", "#818CF8", "#8B5CF6", "#10B981"]}
            ))
            fig_fun.update_layout(
                margin=dict(l=10, r=10, t=10, b=10), height=240,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_fun, use_container_width=True, config={'displayModeBar': False})
            
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 1.05rem; font-weight: 700; color: #0F172A; margin-bottom: 10px;'>Average Time to Hire (Days)</h4>", unsafe_allow_html=True)
            # Average Hiring Time Bar Chart
            hiring_time_df = pd.DataFrame([
                {"Role": "Frontend Eng", "Days": 18},
                {"Role": "ML Engineer", "Days": 24},
                {"Role": "Data Analyst", "Days": 16},
                {"Role": "HR Specialist", "Days": 14},
                {"Role": "Sales Executive", "Days": 15}
            ])
            fig_time = px.bar(
                hiring_time_df, x="Days", y="Role", orientation="h",
                color="Days", color_continuous_scale=["#C7D2FE", "#4F46E5"]
            )
            fig_time.update_layout(
                margin=dict(l=10, r=10, t=10, b=10), height=230,
                xaxis_title="Avg Days", yaxis_title=None,
                coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_time, use_container_width=True, config={'displayModeBar': False})

    with col_t1_right:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 1.05rem; font-weight: 700; color: #0F172A; margin-bottom: 10px;'>Recruitment Pipeline Status</h4>", unsafe_allow_html=True)
            # Donut chart
            pipeline_df = pd.DataFrame([
                {"Stage": "New Applied", "Count": 142},
                {"Stage": "AI Screening", "Count": 118},
                {"Stage": "Interview scheduled", "Count": 28},
                {"Stage": "Offers Pending", "Count": 8},
                {"Stage": "Approved & Hired", "Count": 28}
            ])
            fig_pipe = px.pie(
                pipeline_df, values="Count", names="Stage", hole=0.5,
                color_discrete_sequence=["#6366F1", "#818CF8", "#F59E0B", "#8B5CF6", "#10B981"]
            )
            fig_pipe.update_layout(
                margin=dict(l=10, r=10, t=10, b=10), height=530,
                showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pipe, use_container_width=True, config={'displayModeBar': False})

with tab_trends:
    col_t2_left, col_t2_right = st.columns(2)
    
    with col_t2_left:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 1.05rem; font-weight: 700; color: #0F172A; margin-bottom: 10px;'>Hiring Trend (Monthly Hires)</h4>", unsafe_allow_html=True)
            # Hiring Trend Line Chart
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]
            hires = [2, 4, 3, 5, 6, 8, 10]
            fig_hire_line = go.Figure(go.Scatter(
                x=months, y=hires, mode='lines+markers',
                line=dict(color='#10B981', width=3), marker=dict(size=8),
                fill='tozeroy', fillcolor='rgba(16,185,129,0.06)'
            ))
            fig_hire_line.update_layout(
                margin=dict(l=20, r=20, t=10, b=10), height=230,
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#F1F5F9'),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_hire_line, use_container_width=True, config={'displayModeBar': False})
            
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 1.05rem; font-weight: 700; color: #0F172A; margin-bottom: 10px;'>Department Hiring Distribution</h4>", unsafe_allow_html=True)
            # Department Hiring Bar Chart
            dept_hiring_df = pd.DataFrame([
                {"Dept": "Engineering", "Hires": 12},
                {"Dept": "Analytics", "Hires": 6},
                {"Dept": "Design", "Hires": 4},
                {"Dept": "Sales", "Hires": 4},
                {"Dept": "HR", "Hires": 2}
            ])
            fig_dept_bar = px.bar(
                dept_hiring_df, x="Dept", y="Hires",
                color="Hires", color_continuous_scale=["#C7D2FE", "#6366F1"]
            )
            fig_dept_bar.update_layout(
                margin=dict(l=10, r=10, t=10, b=10), height=230,
                xaxis_title=None, yaxis_title="Total Hires",
                coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_dept_bar, use_container_width=True, config={'displayModeBar': False})

    with col_t2_right:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 1.05rem; font-weight: 700; color: #0F172A; margin-bottom: 10px;'>Applications Trend Over Time</h4>", unsafe_allow_html=True)
            # Applications Trend Area Chart
            app_counts = [45, 60, 78, 110, 130, 155, 180]
            fig_app_area = go.Figure(go.Scatter(
                x=months, y=app_counts, mode='lines',
                line=dict(color='#6366F1', width=3),
                fill='tozeroy', fillcolor='rgba(99,102,241,0.08)'
            ))
            fig_app_area.update_layout(
                margin=dict(l=20, r=20, t=10, b=10), height=510,
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#F1F5F9'),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_app_area, use_container_width=True, config={'displayModeBar': False})

with tab_talent:
    col_t3_left, col_t3_right = st.columns(2)
    
    with col_t3_left:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 1.05rem; font-weight: 700; color: #0F172A; margin-bottom: 10px;'>Top Requested Skills in Demand</h4>", unsafe_allow_html=True)
            # Top Skills Bar Chart
            skills_df = pd.DataFrame([
                {"Skill": "Python", "Count": 128},
                {"Skill": "React", "Count": 94},
                {"Skill": "SQL", "Count": 82},
                {"Skill": "FastAPI", "Count": 75},
                {"Skill": "Docker", "Count": 58}
            ])
            fig_skills_bar = px.bar(
                skills_df, x="Count", y="Skill", orientation="h",
                color="Count", color_continuous_scale=["#EEF2FF", "#4F46E5"]
            )
            fig_skills_bar.update_layout(
                margin=dict(l=10, r=10, t=10, b=10), height=230,
                xaxis_title="JDs referencing skill", yaxis_title=None,
                coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            fig_skills_bar.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_skills_bar, use_container_width=True, config={'displayModeBar': False})
            
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 1.05rem; font-weight: 700; color: #0F172A; margin-bottom: 10px;'>Offer Acceptance Distribution</h4>", unsafe_allow_html=True)
            # Offer Acceptance Donut Chart
            offers_df = pd.DataFrame([
                {"Status": "Accepted", "Count": 28},
                {"Status": "Declined", "Count": 4},
                {"Status": "Pending Review", "Count": 6}
            ])
            fig_offers_donut = px.pie(
                offers_df, values="Count", names="Status", hole=0.5,
                color_discrete_sequence=["#10B981", "#EF4444", "#F59E0B"]
            )
            fig_offers_donut.update_layout(
                margin=dict(l=10, r=10, t=10, b=10), height=230,
                showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_offers_donut, use_container_width=True, config={'displayModeBar': False})

    with col_t3_right:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 1.05rem; font-weight: 700; color: #0F172A; margin-bottom: 10px;'>Candidate Acquisition Sources</h4>", unsafe_allow_html=True)
            # Candidate Sources Donut Chart
            sources_df = pd.DataFrame([
                {"Source": "LinkedIn Job Posting", "Count": 168},
                {"Source": "Employee Referrals", "Count": 94},
                {"Source": "Careers Page Portal", "Count": 62},
                {"Source": "External Agencies", "Count": 28}
            ])
            fig_sources_donut = px.pie(
                sources_df, values="Count", names="Source", hole=0.5,
                color_discrete_sequence=["#4F46E5", "#6366F1", "#818CF8", "#C7D2FE"]
            )
            fig_sources_donut.update_layout(
                margin=dict(l=10, r=10, t=10, b=10), height=510,
                showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_sources_donut, use_container_width=True, config={'displayModeBar': False})

with tab_recruiters:
    with st.container(border=True):
        st.markdown("<h4 style='font-size: 1.05rem; font-weight: 700; color: #0F172A; margin-bottom: 10px;'>Recruiter Screening and Hires Performance</h4>", unsafe_allow_html=True)
        # Recruiter Performance Grouped Bar Chart
        fig_recruiter = go.Figure(data=[
            go.Bar(name='Screens Conducted', x=['Ava Morgan', 'Marcus Aurelius', 'Sophia Lin'], y=[45, 30, 25], marker_color='#818CF8'),
            go.Bar(name='Hires Advanced', x=['Ava Morgan', 'Marcus Aurelius', 'Sophia Lin'], y=[12, 8, 5], marker_color='#10B981')
        ])
        fig_recruiter.update_layout(
            barmode='group',
            margin=dict(l=20, r=20, t=20, b=20), height=450,
            xaxis_title="Recruiter Name", yaxis_title="Count",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_recruiter, use_container_width=True, config={'displayModeBar': False})

# Sidebar footer metadata
with st.sidebar:
    st.markdown("""
    <div style="margin-top: 80px; padding: 16px 10px 0 10px; border-top: 1px solid #1E293B;">
        <div style="display: flex; align-items: center; gap: 10px; opacity: 0.85;">
            <div style="background-color: #1E293B; width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #6366F1;">
                <i class="fa-solid fa-rocket"></i>
            </div>
            <div>
                <div style="font-weight: 700; color: #E2E8F0; font-size: 0.78rem;">HirePilot v1.2</div>
                <div style="font-size: 0.65rem; color: #64748B;">Plan: Enterprise</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
