"""
components/employees.py — HirePilot Employee Roster Page
"""
import streamlit as st
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
        Monitor employee progress and skill growth
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

    cs, cd = st.columns([3, 1])
    with cs: search = st.text_input("Search", placeholder="Search by name, role…", label_visibility="collapsed")
    with cd: dept_f = st.selectbox("Dept", ["All Departments","Engineering","Analytics","HR","Sales","Design"], label_visibility="collapsed")

    employees = api_client.get_employees()
    if employees:
        if search: employees = [e for e in employees if search.lower() in e["name"].lower() or search.lower() in e["role"].lower()]
        if dept_f != "All Departments": employees = [e for e in employees if e["department"].lower() == dept_f.lower()]

    drawer_open = st.session_state["selected_employee_id"] is not None
    if drawer_open:
        list_col, drawer_col = st.columns([1.1, 0.9])
    else:
        list_col = st.container(); drawer_col = None

    with list_col:
        st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 12px 0;'>"
                    "<i class='fa-solid fa-people-group' style='color:#6366F1;'></i> Team Members</h4>",
                    unsafe_allow_html=True)
        if not employees:
            st.markdown("<p style='text-align:center;color:#64748B;padding:30px 0;'>No employees found.</p>",
                        unsafe_allow_html=True)
        else:
            for emp in employees:
                ini = "".join(p[0] for p in emp.get("name","E").split()[:2])
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
                                    {emp.get('role')} • {emp.get('department')}</div>
                                <div style="font-size:0.72rem;color:#64748B;margin-top:2px;">
                                    <strong>Manager:</strong> {emp.get('manager')} •
                                    <strong>Joined:</strong> {emp.get('joining_date')}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with ec2:
                        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                        if st.button("View Profile", key=f"vemp_{emp.get('id')}", use_container_width=True):
                            st.session_state["selected_employee_id"] = emp.get("id"); st.rerun()
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

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
                            st.session_state["selected_employee_id"] = None; st.rerun()

                    st.markdown(f"""
                    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:16px;margin-bottom:15px;">
                        <h4 style="margin:0;color:#0F172A;font-weight:800;">{emp.get('name')}</h4>
                        <p style="margin:2px 0 0;font-size:0.8rem;color:#4F46E5;font-weight:600;">{emp.get('role')}</p>
                        <div style="font-size:0.75rem;color:#64748B;margin-top:6px;">
                            Department: <strong>{emp.get('department')}</strong></div>
                    </div>
                    """, unsafe_allow_html=True)

                    t1, t2, t3 = st.tabs(["📈 Performance","⚡ Skills & Projects","📜 Promotions"])

                    with t1:
                        st.markdown(f"- **Reports to:** {emp.get('manager')}")
                        st.markdown(f"- **Joining Date:** {emp.get('joining_date')}")
                        st.markdown("<h5 style='text-align:center;margin-bottom:0;'>Performance Score</h5>",
                                    unsafe_allow_html=True)
                        perf = emp.get("performance_score", 80)
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number", value=perf,
                            gauge={"axis":{"range":[0,100]},"bar":{"color":"#6366F1"},
                                   "bgcolor":"#EEF2FF","borderwidth":0,
                                   "steps":[{"range":[0,60],"color":"#FEE2E2"},
                                             {"range":[60,85],"color":"#FEF3C7"},
                                             {"range":[85,100],"color":"#ECFDF5"}]},
                            number={"suffix":"%","font":{"size":35,"color":"#0F172A"}}
                        ))
                        fig.update_layout(margin=dict(l=20,r=20,t=10,b=10), height=140,
                                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

                    with t2:
                        skills = emp.get("skills", [])
                        if skills:
                            html = "<div style='display:flex;flex-direction:column;gap:10px;margin-bottom:15px;'>"
                            for sk in skills:
                                name = sk.get("name"); prog = sk.get("progress", 75)
                                html += f"""
                                <div>
                                    <div style="display:flex;justify-content:space-between;font-size:0.78rem;
                                                font-weight:600;color:#475569;margin-bottom:2px;">
                                        <span>{name}</span><span>{prog}%</span></div>
                                    <div style="background:#EEF2FF;border-radius:9999px;height:6px;overflow:hidden;">
                                        <div style="background:#6366F1;width:{prog}%;height:100%;border-radius:9999px;"></div>
                                    </div>
                                </div>"""
                            html += "</div>"
                            st.markdown(html, unsafe_allow_html=True)
                        st.markdown("**Assigned Projects:**")
                        for p in emp.get("projects",[]): st.markdown(f"- **{p}**")

                    with t3:
                        promos = emp.get("promotions",[])
                        if promos:
                            html = "<div style='display:flex;flex-direction:column;gap:12px;margin-top:10px;'>"
                            for i, p in enumerate(promos):
                                html += f"""
                                <div style="display:flex;gap:10px;">
                                    <div style="display:flex;flex-direction:column;align-items:center;">
                                        <div style="width:12px;height:12px;border-radius:50%;background:#6366F1;border:2.5px solid #EEF2FF;"></div>
                                        {"<div style='width:1.5px;flex-grow:1;background:#E2E8F0;min-height:15px;'></div>" if i < len(promos)-1 else ""}
                                    </div>
                                    <div style="font-size:0.8rem;color:#334155;font-weight:600;padding-bottom:5px;">{p}</div>
                                </div>"""
                            html += "</div>"
                            st.markdown(html, unsafe_allow_html=True)
                        else:
                            st.markdown("<p style='font-size:0.8rem;color:#64748B;font-style:italic;'>No promotion records.</p>",
                                        unsafe_allow_html=True)
