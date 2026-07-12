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
    page_icon="👥",
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
    st.markdown("#### <i class='fa-solid fa-people-group' style='color:#6366F1;'></i> Team Members", unsafe_allow_html=True)
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
                            <div style="font-size: 0.8rem; color: #4F46E5; font-weight: 600;">{emp.get('role')} • {emp.get('department')}</div>
                            <div style="font-size: 0.72rem; color: #64748B; margin-top:2px;">
                                <strong>Manager:</strong> {emp.get('manager')} • <strong>Joined:</strong> {emp.get('joining_date')}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with c_c2:
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    if st.button("View Profile Details", key=f"view_emp_{emp.get('id')}", use_container_width=True):
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
                    if st.button("✕ Close Profile", key="close_emp_drawer", use_container_width=True):
                        st.session_state.selected_employee_id = None
                        st.rerun()
                        
                st.markdown(f"""
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-bottom: 15px;">
                    <h4 style="margin: 0; color:#0F172A; font-weight:800;">{active_emp.get('name')}</h4>
                    <p style="margin:2px 0 0 0; font-size:0.8rem; color:#4F46E5; font-weight:600;">{active_emp.get('role')}</p>
                    <div style="font-size:0.75rem; color:#64748B; margin-top:6px;">Department: <strong>{active_emp.get('department')}</strong></div>
                </div>
                """, unsafe_allow_html=True)
                
                # Tab Panels
                tab_perf, tab_skills, tab_history = st.tabs(["📈 Performance", "⚡ Skills & Projects", "📜 Promotion History"])
                
                with tab_perf:
                    st.markdown("**Manager & Joining Information:**")
                    st.markdown(f"- **Reports to:** {active_emp.get('manager')}")
                    st.markdown(f"- **Joining Date:** {active_emp.get('joining_date')}")
                    
                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                    st.markdown("<h5 style='text-align:center; margin-bottom:0;'>Performance Index Score</h5>", unsafe_allow_html=True)
                    
                    # Plotly Performance Gauge Chart
                    perf_val = active_emp.get("performance_score", 80)
                    fig_perf = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=perf_val,
                        gauge={
                            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#475569"},
                            'bar': {'color': "#6366F1"},
                            'bgcolor': "#EEF2FF",
                            'borderwidth': 0,
                            'steps': [
                                {'range': [0, 60], 'color': '#FEE2E2'},
                                {'range': [60, 85], 'color': '#FEF3C7'},
                                {'range': [85, 100], 'color': '#ECFDF5'}
                            ],
                        },
                        number={'suffix': "%", 'font': {'size': 35, 'color': '#0F172A', 'weight': 'bold'}},
                    ))
                    fig_perf.update_layout(
                        margin=dict(l=20, r=20, t=10, b=10),
                        height=140,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_perf, use_container_width=True, config={'displayModeBar': False})
                    
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
