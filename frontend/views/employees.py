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
from frontend.services.cache import get_employees_cached
from frontend.services.app_state import AppState
from frontend.components.page_utils import setup_page, render_sidebar_footer

# Page Config
st.set_page_config(
    page_title="Employee Management - HirePilot",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

setup_page("Employee Roster", "Monitor employee progress and skill growth", page_key=__file__)

# State initialization
if "selected_employee_id" not in st.session_state:
    st.session_state.selected_employee_id = None

# Top Section Search & Filters
col_search, col_dept = st.columns([3, 1])
with col_search:
    search = st.text_input("Search Employees", value="", placeholder="Search by name, role...", label_visibility="collapsed")
with col_dept:
    department_filter = st.selectbox("Department Filter", ["All", "Engineering", "Analytics", "HR", "Sales", "Design"], index=0, label_visibility="collapsed")

# Load employees list from backend
employees = api_client.get_employees()

# Apply local search and department filters
if employees:
    if search:
        employees = [e for e in employees if search.lower() in e["name"].lower() or search.lower() in e["role"].lower()]
    if department_filter != "All":
        employees = [e for e in employees if e["department"].lower() == department_filter.lower()]

# Define split-pane layout
is_drawer_open = st.session_state.selected_employee_id is not None
if is_drawer_open:
    list_col, drawer_col = st.columns([1.1, 0.9])
else:
    list_col = st.container()
    drawer_col = None

with list_col:
    st.markdown("#### Team Members", unsafe_allow_html=True)
    if not employees:
        st.markdown("<p style='text-align:center; color:#64748B; padding:30px 0;'>No employees found matching the criteria.</p>", unsafe_allow_html=True)
    else:
        for emp in employees:
            with st.container(border=True):
                c_c1, c_c2 = st.columns([4, 1.2])
                with c_c1:
                    initials = "".join([part[0] for part in emp.get('name', 'E').split()[:2]])
                    st.markdown(f"""
                    <div style="display: flex; gap: 14px; align-items: center;">
                        <div style="width: 42px; height: 42px; border-radius: 50%; background-color: #EEF2FF; border: 1.5px solid #6366F1; display: flex; align-items: center; justify-content: center; font-weight: 800; color: #6366F1; font-size: 14px;">
                            {initials}
                        </div>
                        <div>
                            <div style="font-weight: 800; font-size: 1.05rem; color: #0F172A;">{emp.get('name')}</div>
                            <div style="font-size: 0.8rem; color: #4F46E5; font-weight: 600;">{emp.get('designation')} • {emp.get('department')}</div>
                            <div style="font-size: 0.72rem; color: #64748B; margin-top:2px;">
                                <strong>Email:</strong> {emp.get('email')} • <strong>Phone:</strong> {emp.get('phone')}
                            </div>
                            <div style="font-size: 0.72rem; color: #64748B; margin-top:2px;">
                                <strong>Joined:</strong> {emp.get('joining_date')} • <strong>Status:</strong> {emp.get('status')}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with c_c2:
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    if st.button("View Profile Details", key=f"view_emp_{emp.get('id')}", width="stretch"):
                        st.session_state.selected_employee_id = emp.get('id')
                        st.rerun()
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# --- SPLIT PANE DETAIL DRAWER ---
if drawer_col and st.session_state.selected_employee_id:
    active_emp = api_client.get_employee(st.session_state.selected_employee_id)
    
    if active_emp:
        with drawer_col:
            with st.container(border=True):
                # Header controls
                head_col1, head_col2 = st.columns([7, 3])
                with head_col1:
                    st.markdown("### <i class='fa-solid fa-address-card' style='color:#6366F1;'></i> Employee Profile")
                with head_col2:
                    if st.button("Close Profile", key="close_emp_drawer", width="stretch"):
                        st.session_state.selected_employee_id = None
                        st.rerun()
                        
                st.markdown(f"""
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-bottom: 15px;">
                    <h4 style="margin: 0; color:#0F172A; font-weight:800;">{active_emp.get('name')}</h4>
                    <p style="margin:2px 0 0 0; font-size:0.8rem; color:#4F46E5; font-weight:600;">{active_emp.get('designation')}</p>
                    <div style="font-size:0.75rem; color:#64748B; margin-top:6px;">Department: <strong>{active_emp.get('department')}</strong></div>
                </div>
                """, unsafe_allow_html=True)
                
                # Tab Panels
                tab_perf, tab_skills, tab_history = st.tabs(["Performance", "Skills & Projects", "Promotion History"])
                
                with tab_perf:
                    # ============================================================
                    # PERFORMANCE DASHBOARD - Premium HR Analytics
                    # ============================================================
                    
                    # Generate realistic demo data for this employee
                    import random
                    import hashlib
                    
                    # Use employee ID as seed for consistent but unique data per employee
                    emp_seed = hash(str(active_emp.get("id", 1))) % 10000
                    random.seed(emp_seed)
                    
                    # Generate realistic employee-specific metrics
                    perf_score = active_emp.get("performance_score", random.randint(75, 98))
                    goal_completion = random.randint(75, 98)
                    attendance = round(random.uniform(92.5, 99.8), 1)
                    productivity = random.randint(78, 96)
                    
                    # Monthly performance data (12 months)
                    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                    monthly_scores = [max(60, min(100, perf_score + random.randint(-8, 8))) for _ in range(12)]
                    monthly_tasks = [random.randint(15, 35) for _ in range(12)]
                    
                    # KPI breakdown data
                    kpi_categories = ["Communication", "Technical Skills", "Leadership", "Problem Solving", "Innovation", "Teamwork"]
                    kpi_scores = [random.randint(70, 98) for _ in range(6)]
                    
                    # Goal completion data
                    total_goals = random.randint(15, 25)
                    completed_goals = random.randint(int(total_goals * 0.7), total_goals)
                    remaining_goals = total_goals - completed_goals
                    
                    # Attendance breakdown
                    present_days = random.randint(200, 230)
                    remote_days = random.randint(30, 60)
                    leave_days = random.randint(5, 15)
                    late_days = random.randint(0, 5)
                    total_work_days = present_days + remote_days + leave_days + late_days
                    
                    # Monthly task completion
                    monthly_completed = [random.randint(12, 30) for _ in range(12)]
                    
                    # Skills radar data
                    radar_categories = ["Leadership", "Technical Skills", "Ownership", "Communication", "Innovation", "Execution", "Teamwork"]
                    radar_scores = [random.randint(65, 95) for _ in range(7)]
                    
                    # Quarterly ratings
                    quarters = ["Q1", "Q2", "Q3", "Q4"]
                    quarterly_ratings = [round(random.uniform(3.5, 4.8), 1) for _ in range(4)]
                    
                    # Productivity heatmap data (weeks x days)
                    heatmap_data = [[random.randint(0, 10) for _ in range(5)] for _ in range(12)]
                    
                    # Performance timeline events
                    timeline_events = [
                        {"date": "2024-01-15", "type": "certification", "title": "AWS Solutions Architect Certified", "desc": "Achieved AWS Solutions Architect Associate certification"},
                        {"date": "2024-03-22", "type": "promotion", "title": "Promoted to Senior Engineer", "desc": "Promoted from Software Engineer to Senior Software Engineer"},
                        {"date": "2024-05-10", "type": "training", "title": "Leadership Training Completed", "desc": "Completed 40-hour Advanced Leadership Development Program"},
                        {"date": "2024-07-18", "type": "project", "title": "Project Phoenix - Lead Architect", "desc": "Led architecture design for Project Phoenix serving 500K users"},
                        {"date": "2024-09-05", "type": "review", "title": "Q3 Performance Review - Exceeds Expectations", "desc": "Received 4.7/5.0 rating with special recognition for innovation"},
                        {"date": "2024-11-12", "type": "certification", "title": "Kubernetes Administrator (CKA)", "desc": "Passed Certified Kubernetes Administrator exam"},
                    ]
                    
                    # Sort timeline by date
                    timeline_events.sort(key=lambda x: x["date"])
                    
                    # Department ranking (simulated)
                    dept_rank = random.randint(1, 15)
                    dept_total = random.randint(20, 50)
                    
                    # Promotion readiness
                    promo_readiness = random.randint(65, 95)
                    
                    # Reset random seed
                    random.seed()
                    
                    # ============================================================
                    # SECTION 1 — Performance KPI Cards
                    # ============================================================
                    st.markdown("### Performance Overview")
                    
                    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
                    
                    # KPI Card 1 - Overall Performance Score
                    with kpi_col1:
                        delta = random.randint(-3, 5)
                        trend_icon = "↑" if delta >= 0 else "↓"
                        trend_color = "#10B981" if delta >= 0 else "#EF4444"
                        sparkline_data = [max(60, min(100, perf_score + random.randint(-5, 5))) for _ in range(10)]
                        
                        fig_spark = go.Figure()
                        fig_spark.add_trace(go.Scatter(
                            y=sparkline_data, mode='lines', line=dict(color='#6366F1', width=2),
                            fill='tozeroy', fillcolor='rgba(99, 102, 241, 0.1)'
                        ))
                        fig_spark.update_layout(
                            height=40, margin=dict(l=0, r=0, t=0, b=0),
                            xaxis=dict(visible=False), yaxis=dict(visible=False),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                        )
                        
                        st.markdown(f"""
                        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:16px;">
                            <div style="font-size:0.75rem;color:#64748B;font-weight:500;margin-bottom:4px;">Performance Score</div>
                            <div style="font-size:1.75rem;font-weight:700;color:#0F172A;margin:4px 0;">{perf_score}%</div>
                            <div style="font-size:0.7rem;color:{trend_color};font-weight:600;margin-top:4px;">
                                {trend_icon} {abs(delta)}% from last month
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.plotly_chart(go.Figure(go.Scatter(y=sparkline_data, mode='lines', line=dict(color='#6366F1', width=2), fill='tozeroy', fillcolor='rgba(99,102,241,0.1)')).update_layout(height=35, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(visible=False), yaxis=dict(visible=False), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), config={'displayModeBar': False}, width="stretch")
                    
                    # KPI Card 2 - Goal Completion
                    with kpi_col2:
                        completed = random.randint(15, 22)
                        total = random.randint(18, 25)
                        pct = round(completed / total * 100)
                        delta = random.randint(-2, 4)
                        trend_icon = "↑" if delta >= 0 else "↓"
                        trend_color = "#10B981" if delta >= 0 else "#EF4444"
                        
                        st.markdown(f"""
                        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:16px;">
                            <div style="font-size:0.75rem;color:#64748B;font-weight:500;margin-bottom:4px;">Goal Completion</div>
                            <div style="font-size:1.75rem;font-weight:700;color:#0F172A;margin:4px 0;">{completed} / {total}</div>
                            <div style="font-size:0.85rem;font-weight:600;color:#6366F1;margin:4px 0;">{pct}% Complete</div>
                            <div style="font-size:0.7rem;color:{'#10B981' if delta >= 0 else '#EF4444'};font-weight:600;margin-top:4px;">
                                {'↑' if delta >= 0 else '↓'} {abs(delta)} from last month
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # KPI Card 3 - Attendance
                    with kpi_col3:
                        att = round(random.uniform(94.5, 99.5), 1)
                        delta = round(random.uniform(-0.5, 0.8), 1)
                        trend_icon = "↑" if delta >= 0 else "↓"
                        trend_color = "#10B981" if delta >= 0 else "#EF4444"
                        
                        st.markdown(f"""
                        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:16px;">
                            <div style="font-size:0.75rem;color:#64748B;font-weight:500;margin-bottom:4px;">Attendance Rate</div>
                            <div style="font-size:1.75rem;font-weight:700;color:#0F172A;margin:4px 0;">{att}%</div>
                            <div style="font-size:0.7rem;color:{'#10B981' if delta >= 0 else '#EF4444'};font-weight:600;margin-top:4px;">
                                {trend_icon} {abs(delta)}% from last month
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # KPI Card 4 - Productivity
                    with kpi_col4:
                        prod = random.randint(80, 97)
                        delta = random.randint(-3, 5)
                        trend_icon = "↑" if delta >= 0 else "↓"
                        trend_color = "#10B981" if delta >= 0 else "#EF4444"
                        
                        st.markdown(f"""
                        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:16px;">
                            <div style="font-size:0.75rem;color:#64748B;font-weight:500;margin-bottom:4px;">Productivity Score</div>
                            <div style="font-size:1.75rem;font-weight:700;color:#0F172A;margin:4px 0;">{prod}%</div>
                            <div style="font-size:0.7rem;color:{'#10B981' if delta >= 0 else '#EF4444'};font-weight:600;margin-top:4px;">
                                {'↑' if delta >= 0 else '↓'} {abs(delta)}% from last month
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # ============================================================
                    # SECTION 2 — Performance Analytics (6 Charts)
                    # ============================================================
                    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
                    st.markdown("### Performance Analytics")
                    
                    # Row 1: Monthly Trend + KPI Breakdown
                    chart_col1, chart_col2 = st.columns(2)
                    
                    # Chart 1: Monthly Performance Trend (Line Chart)
                    with chart_col1:
                        st.markdown("#### Monthly Performance Trend")
                        fig_trend = go.Figure()
                        fig_trend.add_trace(go.Scatter(
                            x=months, y=monthly_scores,
                            mode='lines+markers', name='Performance Score',
                            line=dict(color='#6366F1', width=3),
                            marker=dict(size=8, color='#6366F1'),
                            fill='tozeroy', fillcolor='rgba(99, 102, 241, 0.1)'
                        ))
                        fig_trend.add_hline(y=perf_score, line_dash="dash", line_color="#6366F1",
                                           annotation_text=f"Current: {perf_score}", annotation_position="top right")
                        fig_trend.update_layout(
                            height=350, margin=dict(l=10,r=10,t=30,b=20),
                            yaxis=dict(range=[50, 105], title="Score"),
                            xaxis=dict(title="Month"),
                            hovermode='x unified',
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font={'color': "#0F172A", 'family': "Inter"},
                            showlegend=False
                        )
                        st.plotly_chart(fig_trend, width='stretch')
                    
                    # Chart 2: KPI Breakdown (Horizontal Bar Chart)
                    with chart_col2:
                        st.markdown("#### KPI Breakdown")
                        fig_kpi = go.Figure()
                        colors_kpi = ['#6366F1' if v >= 85 else '#F59E0B' if v >= 75 else '#EF4444' for v in kpi_scores]
                        fig_kpi.add_trace(go.Bar(
                            y=kpi_categories, x=kpi_scores,
                            orientation='h', marker_color=colors_kpi,
                            text=[f"{v}%" for v in kpi_scores], textposition='auto',
                            hovertemplate='<b>%{y}</b><br>Score: %{x}%<extra></extra>'
                        ))
                        fig_kpi.update_layout(
                            height=350, margin=dict(l=10,r=10,t=30,b=20),
                            xaxis=dict(range=[0, 105], title="Score"),
                            yaxis=dict(title="", autorange="reversed"),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font={'color': "#0F172A", 'family': "Inter"},
                            showlegend=False
                        )
                        st.plotly_chart(fig_kpi, width='stretch')
                    
                    # Row 2: Goal Completion + Attendance
                    chart_col3, chart_col4 = st.columns(2)
                    
                    # Chart 3: Goal Completion (Donut)
                    with chart_col3:
                        st.markdown("#### Goal Completion")
                        fig_goals = go.Figure()
                        fig_goals.add_trace(go.Pie(
                            labels=['Completed', 'Remaining'],
                            values=[completed_goals, remaining_goals],
                            hole=0.65,
                            marker_colors=['#10B981', '#E2E8F0'],
                            textinfo='label+percent',
                            textfont=dict(size=12, color='#0F172A'),
                            hovertemplate='<b>%{label}</b><br>%{value} goals (%{percent})<extra></extra>'
                        ))
                        fig_goals.update_layout(
                            height=300, margin=dict(l=10,r=10,t=30,b=10),
                            annotations=[dict(text=f'{completed_goals}/{total_goals}', x=0.5, y=0.5, font_size=18, font_weight=700, showarrow=False)],
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font={'color': "#0F172A", 'family': "Inter"},
                            showlegend=False
                        )
                        st.plotly_chart(fig_goals, width='stretch')
                    
                    # Chart 4: Attendance Analytics (Donut)
                    with chart_col4:
                        st.markdown("#### Attendance Analytics")
                        fig_att = go.Figure()
                        fig_att.add_trace(go.Pie(
                            labels=['Present', 'Remote', 'Leave', 'Late'],
                            values=[present_days, remote_days, leave_days, late_days],
                            hole=0.65,
                            marker_colors=['#10B981', '#6366F1', '#F59E0B', '#EF4444'],
                            textinfo='label+percent',
                            textfont=dict(size=11, color='#0F172A'),
                            hovertemplate='<b>%{label}</b><br>%{value} days (%{percent})<extra></extra>'
                        ))
                        fig_att.update_layout(
                            height=300, margin=dict(l=10,r=10,t=30,b=10),
                            annotations=[dict(text=f'{total_work_days} days', x=0.5, y=0.5, font_size=16, font_weight=700, showarrow=False)],
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font={'color': "#0F172A", 'family': "Inter"},
                            showlegend=False
                        )
                        st.plotly_chart(fig_att, width='stretch')
                    
                    # Row 3: Task Completion + Skills Radar
                    chart_col5, chart_col6 = st.columns(2)
                    
                    # Chart 5: Monthly Task Completion (Area Chart)
                    with chart_col5:
                        st.markdown("#### Monthly Task Completion")
                        fig_tasks = go.Figure()
                        fig_tasks.add_trace(go.Scatter(
                            x=months, y=monthly_completed,
                            mode='lines+markers', name='Tasks Completed',
                            line=dict(color='#10B981', width=3),
                            marker=dict(size=8, color='#10B981'),
                            fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'
                        ))
                        fig_tasks.update_layout(
                            height=350, margin=dict(l=10,r=10,t=30,b=20),
                            yaxis=dict(range=[0, max(monthly_completed)*1.2], title="Tasks"),
                            xaxis=dict(title="Month"),
                            hovermode='x unified',
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font={'color': "#0F172A", 'family': "Inter"},
                            showlegend=False
                        )
                        st.plotly_chart(fig_tasks, width='stretch')
                    
                    # Chart 6: Skills Assessment (Radar Chart)
                    with chart_col6:
                        st.markdown("#### Skills Assessment")
                        fig_radar = go.Figure()
                        fig_radar.add_trace(go.Scatterpolar(
                            r=radar_scores, theta=radar_categories,
                            fill='toself', name='Current Level',
                            line=dict(color='#6366F1', width=2),
                            fillcolor='rgba(99, 102, 241, 0.2)'
                        ))
                        fig_radar.add_trace(go.Scatterpolar(
                            r=[90]*7, theta=radar_categories,
                            fill='toself', name='Target Level',
                            line=dict(color='#10B981', width=2, dash='dash'),
                            fillcolor='rgba(16, 185, 129, 0.1)'
                        ))
                        fig_radar.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=8))),
                            height=350, margin=dict(l=20,r=20,t=30,b=20),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font={'color': "#0F172A", 'family': "Inter"},
                            showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.15, x=0.5)
                        )
                        st.plotly_chart(fig_radar, width='stretch')
                    
                    # ============================================================
                    # SECTION 3 — Performance Summary
                    # ============================================================
                    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
                    st.markdown("### Performance Summary")
                    
                    sum_col1, sum_col2, sum_col3 = st.columns(3)
                    
                    with sum_col1:
                        st.markdown(f"""
                        <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:12px;padding:16px;">
                            <div style="font-size:0.75rem;color:#166534;font-weight:600;margin-bottom:8px;">Strengths</div>
                            <ul style="margin:0;padding-left:20px;color:#166534;font-size:0.85rem;line-height:1.8;">
                                <li>Consistently exceeds performance targets</li>
                                <li>Strong technical leadership and mentorship</li>
                                <li>Excellent cross-functional collaboration</li>
                                <li>Proactive problem identification and resolution</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with sum_col2:
                        st.markdown(f"""
                        <div style="background:#FEF3C7;border:1px solid #FDE68A;border-radius:12px;padding:16px;">
                            <div style="font-size:0.75rem;color:#92400E;font-weight:600;margin-bottom:8px;">Areas for Improvement</div>
                            <ul style="margin:0;padding-left:20px;color:#92400E;font-size:0.85rem;line-height:1.8;">
                                <li>Increase cross-functional visibility</li>
                                <li>Develop strategic planning capabilities</li>
                                <li>Expand external industry engagement</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with sum_col3:
                        st.markdown(f"""
                        <div style="background:#EEF2FF;border:1px solid #C7D2FE;border-radius:12px;padding:16px;">
                            <div style="font-size:0.75rem;color:#4338CA;font-weight:600;margin-bottom:8px;">Current Rating & Readiness</div>
                            <div style="font-size:1.5rem;font-weight:700;color:#4338CA;margin:4px 0;">{perf_score}/100</div>
                            <div style="font-size:0.8rem;color:#4338CA;margin:4px 0;">Department Rank: #{dept_rank} of {dept_total}</div>
                            <div style="font-size:0.8rem;color:#4338CA;margin:4px 0;">Promotion Readiness: {promo_readiness}%</div>
                            <div style="font-size:0.8rem;color:#4338CA;margin:4px 0;">Next Review: Q1 2025</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # ============================================================
                    # SECTION 4 — Performance Timeline
                    # ============================================================
                    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
                    st.markdown("### Performance Timeline")
                    
                    for event in timeline_events:
                        type_colors = {
                            "certification": ("#F0FDF4", "#22C55E", "fa-certificate"),
                            "promotion": ("#FEF3C7", "#F59E0B", "fa-arrow-up"),
                            "training": ("#EEF2FF", "#6366F1", "fa-graduation-cap"),
                            "project": ("#F0FDF4", "#10B981", "fa-project-diagram"),
                            "review": ("#FEF3C7", "#F59E0B", "fa-star"),
                        }
                        bg, color, icon = type_colors.get(event["type"], ("#F3F4F6", "#6B7280", "fa-circle"))
                        
                        st.markdown(f"""
                        <div style="display:flex;gap:16px;padding:16px;background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;margin-bottom:12px;">
                            <div style="width:44px;height:44px;border-radius:10px;background:{bg};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                                <i class="fa-solid {icon}" style="color:{color};font-size:1.1rem;"></i>
                            </div>
                            <div style="flex:1;">
                                <div style="font-weight:700;color:#0F172A;font-size:0.95rem;">{event['title']}</div>
                                <div style="color:#64748B;font-size:0.85rem;margin-top:2px;">{event['desc']}</div>
                                <div style="color:#94A3B8;font-size:0.75rem;margin-top:4px;">{event['date']}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # ============================================================
                    # SECTION 5 — Additional Analytics (Quarterly + Heatmap)
                    # ============================================================
                    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
                    st.markdown("### Additional Analytics")
                    
                    add_col1, add_col2 = st.columns(2)
                    
                    # Quarterly Rating Trend
                    with add_col1:
                        st.markdown("#### Quarterly Rating Trend")
                        fig_quarter = go.Figure()
                        fig_quarter.add_trace(go.Scatter(
                            x=quarters, y=quarterly_ratings,
                            mode='lines+markers', name='Rating',
                            line=dict(color='#6366F1', width=3),
                            marker=dict(size=10, color='#6366F1'),
                            fill='tozeroy', fillcolor='rgba(99, 102, 241, 0.1)'
                        ))
                        fig_quarter.add_hline(y=4.0, line_dash="dash", line_color="#10B981",
                                             annotation_text="Target: 4.0", annotation_position="bottom right")
                        fig_quarter.update_layout(
                            height=300, margin=dict(l=10,r=10,t=30,b=20),
                            yaxis=dict(range=[3.0, 5.0], title="Rating"),
                            xaxis=dict(title="Quarter"),
                            hovermode='x unified',
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font={'color': "#0F172A", 'family': "Inter"},
                            showlegend=False
                        )
                        st.plotly_chart(fig_quarter, width='stretch')
                    
                    # Productivity Heatmap
                    with add_col2:
                        st.markdown("#### Productivity Heatmap (12 Weeks × 5 Days)")
                        fig_heat = go.Figure()
                        fig_heat.add_trace(go.Heatmap(
                            z=heatmap_data,
                            x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                            y=[f'Week {i+1}' for i in range(12)],
                            colorscale=[[0, '#FEE2E2'], [0.3, '#FEF3C7'], [0.6, '#D1FAE5'], [1, '#A7F3D0']],
                            showscale=False,
                            hovertemplate='Week %{y}<br>%{x}<br>Productivity: %{z}/10<extra></extra>'
                        ))
                        fig_heat.update_layout(
                            height=300, margin=dict(l=10,r=10,t=30,b=20),
                            xaxis=dict(title="", side="top"),
                            yaxis=dict(title="", autorange="reversed"),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font={'color': "#0F172A", 'family': "Inter"}
                        )
                        st.plotly_chart(fig_heat, width='stretch')
                    
                with tab_skills:
                    st.markdown("**Active Skill Set & Progress:**")
                    skills_list = active_emp.get("skills", [])
                    if skills_list:
                        skills_html = "<div style='display: flex; flex-direction: column; gap: 10px; margin-top:5px; margin-bottom:15px;'>"
                        for skill in skills_list:
                            name = skill.get("name")
                            prog = skill.get("progress", 75)
                            skills_html += f"""
                            <div>
                                <div style="display: flex; justify-content: space-between; font-size: 0.78rem; font-weight: 600; color: #475569; margin-bottom: 2px;">
                                    <span>{name}</span>
                                    <span>{prog}%</span>
                                </div>
                                <div style="background-color: #EEF2FF; border-radius: 9999px; height: 6px; width: 100%; overflow: hidden;">
                                    <div style="background-color: #6366F1; width: {prog}%; height: 100%; border-radius: 9999px;"></div>
                                </div>
                            </div>
                            """
                        skills_html += "</div>"
                        st.markdown(skills_html, unsafe_allow_html=True)
                    else:
                        st.write("No skills progress tracked.")
                        
                    st.markdown("**Assigned Projects:**")
                    projects_list = active_emp.get("projects", [])
                    if projects_list:
                        for proj in projects_list:
                            st.markdown(f"- <span style='font-size:0.82rem; color:#334155; font-weight:600;'>{proj}</span>", unsafe_allow_html=True)
                    else:
                        st.write("No projects assigned.")
                        
                with tab_history:
                    st.markdown("**Promotion Timeline:**")
                    promotions = active_emp.get("promotions", [])
                    if promotions:
                        promotions_html = "<div style='display: flex; flex-direction: column; gap: 12px; margin-top: 10px;'>"
                        for idx, p in enumerate(promotions):
                            promotions_html += f"""
                            <div style="display: flex; gap: 10px;">
                                <div style="display: flex; flex-direction: column; align-items: center;">
                                    <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #6366F1; border: 2.5px solid #EEF2FF;"></div>
                                    { '<div style="width: 1.5px; flex-grow: 1; background-color: #E2E8F0; min-height: 15px;"></div>' if idx < len(promotions)-1 else '' }
                                </div>
                                <div style="font-size: 0.8rem; color: #334155; font-weight: 600; padding-bottom:5px;">
                                    {p}
                                </div>
                            </div>
                            """
                        promotions_html += "</div>"
                        st.markdown(promotions_html, unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>No previous promotion records.</p>", unsafe_allow_html=True)
