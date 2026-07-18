import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from frontend.components import api_client

def render_employees() -> None:
    if "selected_employee_id" not in st.session_state:
        st.session_state["selected_employee_id"] = None

    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        👨‍💼 Employee Roster
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

    drawer_open = st.session_state["selected_employee_id"] is not None
    if drawer_open:
        list_col, drawer_col = st.columns([1.1, 1.3])
    else:
        list_col = st.container()
        drawer_col = None

    with list_col:
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
                                    {emp.get('designation', 'Employee')} • {emp.get('department', 'Unassigned')}</div>
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

    # ── Drawer ────────────────────────────────────────────────────────────
    if drawer_col and st.session_state["selected_employee_id"]:
        emp = api_client.get_employee(st.session_state["selected_employee_id"])
        if emp:
            with drawer_col:
                with st.container(border=True):
                    eh1, eh2 = st.columns([7, 3])
                    with eh1:
                        st.markdown("<h3><i class='fa-solid fa-address-card' style='color:#6366F1;'></i> Employee Profile</h3>",
                                    unsafe_allow_html=True)
                    with eh2:
                        if st.button("✕ Close", key="close_emp", use_container_width=True):
                            st.session_state["selected_employee_id"] = None
                            st.rerun()

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

                    t1, t2, t3, t4 = st.tabs(["⚡ Skills & Projects", "📈 Performance", "🧠 AI Talent Insights", "⚙️ Actions"])

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
                                st.markdown(f"""
                                <div style="background:#FFF;border:1px solid #E2E8F0;padding:12px;border-radius:8px;margin-bottom:10px;">
                                    <div style="font-weight:700;font-size:0.9rem;">{p.get('name')}</div>
                                    <div style="font-size:0.8rem;color:#64748B;margin-top:4px;">
                                        Role: {p.get('role')} | Client: {p.get('client', 'Internal')}
                                    </div>
                                    <div style="font-size:0.8rem;color:#475569;margin-top:6px;">{p.get('description', '')}</div>
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

                        if st.button("🔄 Refresh Insights", use_container_width=True):
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
                        # Export stub
                        if st.button("📥 Download Employee Report (PDF)", use_container_width=True):
                            report = api_client.get_employee_performance_summary(emp.get("id")) # We'll replace with export API
                            st.success(f"Report would be downloaded for {emp.get('name')}")
