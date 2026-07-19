import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from frontend.components import api_client


def _render_employee_profile(emp):
    """Render the employee profile view with tabs."""
    st.markdown(f"""
    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:16px;margin-bottom:15px;">
        <h4 style="margin:0;color:#0F172A;font-weight:800;">{emp.get('name')}</h4>
        <p style="margin:2px 0 0;font-size:0.8rem;color:#4F46E5;font-weight:600;">{emp.get('designation', 'Employee')}</p>
        <div style="font-size:0.75rem;color:#64748B;margin-top:6px;">
            Department: <strong>{emp.get('department', 'N/A')}</strong> | 
            Location: <strong>{emp.get('work_location', 'Remote')}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs(["âš¡ Skills & Projects", "ðŸ“ˆ Performance", "ðŸ§  AI Talent Insights", "âš™ï¸ Actions"])

    with t1:
        st.markdown("**Skills:**")
        skills = emp.get("skills", [])
        if skills:
            html = "<div style='display:flex;flex-wrap:wrap;gap:8px;margin-bottom:15px;'>"
            for sk in skills:
                name = sk.get("name")
                prog = sk.get("proficiency", 50)
                html += f"""
                <div style="background:#EEF2FF;border:1px solid #C7D2FE;color:#4338CA;
                            padding:4px 10px;border-radius:16px;font-size:0.75rem;font-weight:600;">
                    {name} <span style="opacity:0.6;font-size:0.7rem;">({prog}%)</span>
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("No skills recorded.")

        st.markdown("**Assigned Projects:**")
        projects = emp.get("projects", [])
        if projects:
            for p in projects:
                # Handle both string and dict formats for backward compatibility
                if isinstance(p, dict):
                    name = p.get('name', 'Unnamed Project')
                    role = p.get('role', '')
                    client = p.get('client', 'Internal')
                    description = p.get('description', '')
                else:
                    name = str(p)
                    role = ''
                    client = 'Internal'
                    description = ''
                
                st.markdown(f"""
                <div style="background:#FFF;border:1px solid #E2E8F0;padding:12px;border-radius:8px;margin-bottom:10px;">
                    <div style="font-weight:700;font-size:0.9rem;">{name}</div>
                    <div style="font-size:0.8rem;color:#64748B;margin-top:4px;">
                        Role: {role} | Client: {client}
                    </div>
                    <div style="font-size:0.8rem;color:#475569;margin-top:6px;">{description}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No projects assigned.")

    with t2:
        perf_summary = api_client.get_employee_performance_summary(emp.get("id"))
        if perf_summary and perf_summary.get("history"):
            hist = perf_summary["history"]
            score = perf_summary.get("overall_score", 0)
            
            st.markdown(f"<h5 style='text-align:center;'>Average KPI Score: {score}/100</h5>", unsafe_allow_html=True)
            
            # Trend chart
            df = pd.DataFrame(hist)
            df["period"] = df["month"] + " " + df["year"].astype(str)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["period"], y=df["kpi_score"], mode="lines+markers", name="KPI Score",
                                     line=dict(color="#6366F1", width=3)))
            fig.update_layout(margin=dict(l=10,r=10,t=30,b=20), height=200, yaxis=dict(range=[0,100]))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data available.")

    with t3:
        st.markdown("**AI-Driven Talent Insights**")
        st.write("Deep analysis of technical growth, leadership potential, and productivity.")
        
        insights = emp.get("talent_insights", {})
        if not insights:
            st.warning("No insights available. Click the button below to generate them.")
        else:
            st.markdown(f"""
            <div style="background:#F0FDF4;border:1px solid #BBF7D0;padding:12px;border-radius:8px;margin-bottom:12px;">
                <strong><i class="fa-solid fa-star" style="color:#22C55E;"></i> Overall Rating:</strong> {insights.get('rating', 'N/A')}
                (Score: {insights.get('overall_talent_score', 'N/A')}/100)
            </div>
            <div style="font-size:0.85rem;">
                <strong>Executive Summary:</strong> {insights.get('executive_summary', 'N/A')}<br><br>
                <strong>Technical:</strong> {insights.get('technical_assessment', 'N/A')}<br><br>
                <strong>Leadership:</strong> {insights.get('leadership_assessment', 'N/A')}<br><br>
                <strong>Career Growth:</strong> 
                Promotion Readiness: {insights.get('career_growth', {}).get('promotion_readiness', 'N/A')} | 
                Next Role: {insights.get('career_growth', {}).get('suggested_next_role', 'N/A')}
            </div>
            """, unsafe_allow_html=True)

        if st.button("ðŸ”„ Refresh Insights", use_container_width=True):
            with st.spinner("Generating deep AI insights..."):
                res = api_client.generate_talent_insights(emp.get("id"))
                if res:
                    st.success("Insights updated successfully!")
                    st.rerun()

    with t4:
        st.markdown("**Management Actions**")
        # Basic stubs for actions
        act_col1, act_col2 = st.columns(2)
        with act_col1:
            if st.button("Assign Project", use_container_width=True):
                st.info("Stub: Open Project Assignment Modal")
        with act_col2:
            if st.button("Log Performance", use_container_width=True):
                st.info("Stub: Open Performance Logging Modal")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Edit Employee Profile
        if st.button("âœï¸ Edit Profile", use_container_width=True):
            st.session_state["edit_employee_id"] = emp.get("id")
            st.rerun()
        
        # Export stub
        if st.button("ðŸ“¥ Download Employee Report (PDF)", use_container_width=True):
            report = api_client.get_employee_performance_summary(emp.get("id")) # We'll replace with export API
            st.success(f"Report would be downloaded for {emp.get('name')}")


def _render_edit_employee_form(emp):
    """Render the edit form for employee profile."""
    st.markdown("### âœï¸ Edit Employee Profile")
    
    with st.form(f"edit_employee_{emp.get('id')}"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", value=emp.get("name", ""))
            email = st.text_input("Email", value=emp.get("email", ""))
            phone = st.text_input("Phone", value=emp.get("phone", ""))
            department = st.selectbox("Department", 
                ["Engineering", "Analytics", "HR", "Sales", "Design", "Marketing", "Finance"],
                index=["Engineering", "Analytics", "HR", "Sales", "Design", "Marketing", "Finance"].index(emp.get("department", "Engineering")) if emp.get("department") in ["Engineering", "Analytics", "HR", "Sales", "Design", "Marketing", "Finance"] else 0)
            designation = st.text_input("Designation", value=emp.get("designation", ""))
        with col2:
            work_location = st.selectbox("Work Location", 
                ["Remote", "Hybrid", "On-site"],
                index=["Remote", "Hybrid", "On-site"].index(emp.get("work_location", "Remote")) if emp.get("work_location") in ["Remote", "Hybrid", "On-site"] else 0)
            joining_date = st.date_input("Joining Date", value=emp.get("joining_date", ""))
            status = st.selectbox("Status", 
                ["Active", "On Leave", "Ex-Employee"],
                index=["Active", "On Leave", "Ex-Employee"].index(emp.get("status", "Active")) if emp.get("status") in ["Active", "On Leave", "Ex-Employee"] else 0)
            reporting_manager = st.text_input("Reporting Manager", value=emp.get("reporting_manager", ""))
            current_project = st.text_input("Current Project", value=emp.get("current_project", ""))
        
        st.markdown("**Skills:**")
        skills = emp.get("skills", [])
        if skills:
            for i, skill in enumerate(skills):
                col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
                with col_s1:
                    skill_name = st.text_input(f"Skill {i+1} Name", value=skill.get("name", ""), key=f"skill_name_{i}")
                with col_s2:
                    proficiency = st.number_input(f"Proficiency %", value=skill.get("proficiency", 50), min_value=0, max_value=100, key=f"skill_prof_{i}")
                with col_s3:
                    skill_status = st.selectbox(f"Status", ["Acquired", "Learning", "Planned"], 
                        index=["Acquired", "Learning", "Planned"].index(skill.get("status", "Acquired")) if skill.get("status") in ["Acquired", "Learning", "Planned"] else 0,
                        key=f"skill_status_{i}")
        
        st.markdown("**Projects:**")
        projects = emp.get("projects", [])
        if projects:
            for i, proj in enumerate(projects):
                if isinstance(proj, dict):
                    proj_name = st.text_input(f"Project {i+1} Name", value=proj.get("name", ""), key=f"proj_name_{i}")
                    proj_role = st.text_input(f"Role", value=proj.get("role", ""), key=f"proj_role_{i}")
                    proj_client = st.text_input(f"Client", value=proj.get("client", "Internal"), key=f"proj_client_{i}")
                    proj_desc = st.text_area(f"Description", value=proj.get("description", ""), key=f"proj_desc_{i}")
                else:
                    proj_name = st.text_input(f"Project {i+1} Name", value=str(proj), key=f"proj_name_{i}")
                    proj_role = st.text_input(f"Role", value="", key=f"proj_role_{i}")
                    proj_client = st.text_input(f"Client", value="Internal", key=f"proj_client_{i}")
                    proj_desc = st.text_area(f"Description", value="", key=f"proj_desc_{i}")
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.form_submit_button("ðŸ’¾ Save Changes", type="primary", use_container_width=True):
                # TODO: Implement save logic
                st.success("Profile updated successfully!")
                st.session_state.pop("edit_employee_id", None)
                st.rerun()
        with col_cancel:
            if st.form_submit_button("âœ• Cancel", use_container_width=True):
                st.session_state.pop("edit_employee_id", None)
                st.rerun()


def render_employees() -> None:
    if "selected_employee_id" not in st.session_state:
        st.session_state["selected_employee_id"] = None

    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        ðŸ‘¨â€ðŸ’¼ Employee Roster
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        Monitor employee progress, performance, and AI-driven talent insights.
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

    cs, cd, cr = st.columns([3, 1.5, 1.5])
    with cs: search = st.text_input("Search", placeholder="Search by name, email...", label_visibility="collapsed")
    with cd: dept_f = st.selectbox("Department", ["All", "Engineering", "Analytics", "HR", "Sales", "Design"], label_visibility="collapsed")
    with cr: stat_f = st.selectbox("Status", ["All", "Active", "On Leave", "Ex-Employee"], label_visibility="collapsed")

    employees = api_client.get_employees()
    if employees:
        if search:
            like = search.lower()
            employees = [e for e in employees if like in e.get("name", "").lower() or like in e.get("email", "").lower()]
        if dept_f != "All":
            employees = [e for e in employees if e.get("department") == dept_f]
        if stat_f != "All":
            employees = [e for e in employees if e.get("status") == stat_f]

    # Main tabs: Team Members and Employee Profile (when selected)
    if st.session_state["selected_employee_id"]:
        tab_team, tab_profile = st.tabs(["ðŸ‘¥ Team Members", "ðŸ‘¤ Employee Profile"])
    else:
        tab_team = st.container()
        tab_profile = None

    with tab_team:
        st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 12px 0;'>"
                    "<i class='fa-solid fa-people-group' style='color:#6366F1;'></i> Team Members</h4>",
                    unsafe_allow_html=True)
        if not employees:
            st.markdown("<p style='text-align:center;color:#64748B;padding:30px 0;'>No employees found.</p>",
                        unsafe_allow_html=True)
        else:
            for emp in employees:
                ini = "".join(p[0] for p in emp.get("name","E").split()[:2]).upper()
                with st.container(border=True):
                    ec1, ec2 = st.columns([4, 1.2])
                    with ec1:
                        st.markdown(f"""
                        <div style="display:flex;gap:14px;align-items:center;">
                            <div style="width:42px;height:42px;border-radius:50%;background:#EEF2FF;
                                        border:1.5px solid #6366F1;display:flex;align-items:center;
                                        justify-content:center;font-weight:800;color:#6366F1;font-size:14px;">
                                {ini}</div>
                            <div>
                                <div style="font-weight:800;font-size:1rem;color:#0F172A;">{emp.get('name')}</div>
                                <div style="font-size:0.8rem;color:#4F46E5;font-weight:600;">
                                    {emp.get('designation', 'Employee')} â€¢ {emp.get('department', 'Unassigned')}</div>
                                <div style="font-size:0.72rem;color:#64748B;margin-top:2px;">
                                    <strong>Joined:</strong> {emp.get('joining_date', 'N/A')}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with ec2:
                        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                        if st.button("View Profile", key=f"vemp_{emp.get('id')}", use_container_width=True):
                            st.session_state["selected_employee_id"] = emp.get("id")
                            st.rerun()
                st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # Employee Profile Tab
    if tab_profile and st.session_state["selected_employee_id"]:
        emp = api_client.get_employee(st.session_state["selected_employee_id"])
        if emp:
            with tab_profile:
                # Header with close button
                eh1, eh2 = st.columns([7, 3])
                with eh1:
                    st.markdown("<h3><i class='fa-solid fa-address-card' style='color:#6366F1;'></i> Employee Profile</h3>",
                                unsafe_allow_html=True)
                with eh2:
                    if st.button("â† Back to Team", key="close_emp", use_container_width=True):
                        st.session_state["selected_employee_id"] = None
                        st.session_state.pop("edit_employee_id", None)
                        st.rerun()

                # Edit mode
                if st.session_state.get("edit_employee_id") == emp.get("id"):
                    _render_edit_employee_form(emp)
                else:
                    _render_employee_profile(emp)
