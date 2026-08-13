"""
components/analytics.py — HirePilot Analytics Page
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from frontend.components import api_client


def render_analytics() -> None:
    # Fetch live data
    data = api_client.get_analytics_bundle() or {}
    funnel = data.get("funnel", {})
    velocity = data.get("velocity", [])
    workforce = data.get("workforce", {})
    
    time_to_hire_data = data.get("time_to_hire", [])
    pipeline_status_data = data.get("pipeline_status", [])
    top_skills_data = data.get("top_skills", [])
    acquisition_sources_data = data.get("acquisition_sources", [])
    recruiter_performance_data = data.get("recruiter_performance", [])
    
    # Process Velocity for Trends (Monthly)
    df_vel = pd.DataFrame(velocity)
    if not df_vel.empty and "date" in df_vel.columns:
        df_vel["date"] = pd.to_datetime(df_vel["date"])
        df_vel["Month"] = df_vel["date"].dt.strftime("%b")
        df_vel_monthly = df_vel.groupby("Month", sort=False).sum(numeric_only=True).reset_index()
        months_list = df_vel_monthly["Month"].tolist()
        hires_trend = df_vel_monthly["Hires"].tolist()
        apps_trend = df_vel_monthly["Applications"].tolist()
    else:
        months_list = ["Jan","Feb","Mar","Apr","May","Jun","Jul"]
        hires_trend = [0] * 7
        apps_trend = [0] * 7

    applied_val = funnel.get("Applied", 0)
    screened_val = funnel.get("Screened", 0)
    interviewed_val = funnel.get("Interview", 0)
    shortlisted_val = funnel.get("Offer", 0)
    hired_val = funnel.get("Hired", 0)

    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        📊 Analytics Dashboard
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        Interactive recruitment statistics and reporting
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

    # KPI Row (Growth is still mocked as backend doesn't provide historical deltas)
    kpi = st.columns(4)
    for col, icon, color, bg, title, val, growth, up in [
        (kpi[0], "fa-folder-open",   "#6366F1", "#EEF2FF", "Total Applications", str(applied_val),  "↑ 12%", True),
        (kpi[1], "fa-calendar-days", "#F59E0B", "#FEF3C7", "Interviewed",         str(interviewed_val),   "↑ 8%",  True),
        (kpi[2], "fa-star",          "#8B5CF6", "#F5F3FF", "Shortlisted",         str(shortlisted_val),   "↑ 4%",  True),
        (kpi[3], "fa-circle-check",  "#10B981", "#ECFDF5", "Hired",               str(hired_val),   "↑ 18%", True),
    ]:
        g_class = "growth-up" if up else "growth-down"
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color:{color};">
                <div class="kpi-icon-wrapper" style="color:{color};background:{bg};">
                    <i class="fa-solid {icon}"></i></div>
                <div class="kpi-title">{title}</div>
                <div class="kpi-value">{val}</div>
                <div class="kpi-growth {g_class}"><span>{growth}</span>
                    <span style="color:#94A3B8;font-weight:500;">vs last month</span></div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    tab_funnel, tab_trends, tab_talent, tab_recruiters = st.tabs([
        "Pipeline & Funnel", "Trends & Departments",
        "Talent & Channels",  "Recruiter Analytics"
    ])

    with tab_funnel:
        col_l, col_r = st.columns(2)
        with col_l:
            with st.container(border=True):
                st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>Hiring Funnel Conversion</h4>",
                            unsafe_allow_html=True)
                fig = go.Figure(go.Funnel(
                    y=["Applied","Screened","Interviewed","Shortlisted","Hired"],
                    x=[applied_val, screened_val, interviewed_val, shortlisted_val, hired_val],
                    textinfo="value+percent initial",
                    connector={"fillcolor":"#EEF2FF"},
                    marker={"color":["#4F46E5","#6366F1","#818CF8","#8B5CF6","#10B981"]}
                ))
                fig.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=240,
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, width="stretch", config={"displayModeBar":False})
            st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>Average Time to Hire</h4>",
                            unsafe_allow_html=True)
                
                if time_to_hire_data:
                    df = pd.DataFrame(time_to_hire_data)
                else:
                    df = pd.DataFrame([{"Role":"Frontend Eng","Days":18},{"Role":"ML Engineer","Days":24},
                                       {"Role":"Data Analyst","Days":16},{"Role":"HR Specialist","Days":14},{"Role":"Sales Exec","Days":15}])
                fig2 = px.bar(df, x="Days", y="Role", orientation="h", color="Days",
                              color_continuous_scale=["#C7D2FE","#4F46E5"])
                fig2.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=230,
                                   xaxis_title="Avg Days", yaxis_title=None, coloraxis_showscale=False,
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, width="stretch", config={"displayModeBar":False})

        with col_r:
            with st.container(border=True):
                st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>Recruitment Pipeline Status</h4>",
                            unsafe_allow_html=True)
                
                if pipeline_status_data:
                    df2 = pd.DataFrame(pipeline_status_data)
                else:
                    df2 = pd.DataFrame([{"Stage":"New Applied","Count":142},{"Stage":"AI Screening","Count":118},
                                        {"Stage":"Interview Scheduled","Count":28},{"Stage":"Offers Pending","Count":8},
                                        {"Stage":"Approved & Hired","Count":28}])
                fig3 = px.pie(df2, values="Count", names="Stage", hole=0.5,
                              color_discrete_sequence=["#6366F1","#818CF8","#F59E0B","#8B5CF6","#10B981"])
                fig3.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=530,
                                   showlegend=True, legend=dict(orientation="h",yanchor="bottom",y=-0.15,xanchor="center",x=0.5),
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig3, width="stretch", config={"displayModeBar":False})

    with tab_trends:
        col_l, col_r = st.columns(2)
        with col_l:
            with st.container(border=True):
                st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>Hiring Trend (Monthly)</h4>",
                            unsafe_allow_html=True)
                fig = go.Figure(go.Scatter(x=months_list, y=hires_trend,
                                           mode="lines+markers", line=dict(color="#10B981",width=3),
                                           fill="tozeroy", fillcolor="rgba(16,185,129,0.06)"))
                fig.update_layout(margin=dict(l=20,r=20,t=10,b=10), height=230,
                                  xaxis=dict(showgrid=False), yaxis=dict(showgrid=True,gridcolor="#F1F5F9"),
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, width="stretch", config={"displayModeBar":False})
            st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>Department Distribution</h4>",
                            unsafe_allow_html=True)
                dept_dict = workforce.get("by_department", {})
                if not dept_dict: dept_dict = {"None": 0}
                df_dept = pd.DataFrame([{"Dept": k, "Hires": v} for k, v in dept_dict.items()])
                fig2 = px.bar(df_dept, x="Dept", y="Hires", color="Hires", color_continuous_scale=["#C7D2FE","#6366F1"])
                fig2.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=230,
                                   xaxis_title=None, yaxis_title="Total Hires", coloraxis_showscale=False,
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, width="stretch", config={"displayModeBar":False})
        with col_r:
            with st.container(border=True):
                st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>Applications Over Time</h4>",
                            unsafe_allow_html=True)
                fig3 = go.Figure(go.Scatter(x=months_list, y=apps_trend,
                                            mode="lines", line=dict(color="#6366F1",width=3),
                                            fill="tozeroy", fillcolor="rgba(99,102,241,0.08)"))
                fig3.update_layout(margin=dict(l=20,r=20,t=10,b=10), height=510,
                                   xaxis=dict(showgrid=False), yaxis=dict(showgrid=True,gridcolor="#F1F5F9"),
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig3, width="stretch", config={"displayModeBar":False})

    with tab_talent:
        col_l, col_r = st.columns(2)
        with col_l:
            with st.container(border=True):
                st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>Top Skills in Demand</h4>",
                            unsafe_allow_html=True)
                
                if top_skills_data:
                    df = pd.DataFrame(top_skills_data)
                else:
                    df = pd.DataFrame([{"Skill":"Python","Count":128},{"Skill":"React","Count":94},
                                       {"Skill":"SQL","Count":82},{"Skill":"FastAPI","Count":75},{"Skill":"Docker","Count":58}])
                fig = px.bar(df, x="Count", y="Skill", orientation="h", color="Count",
                             color_continuous_scale=["#EEF2FF","#4F46E5"])
                fig.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=230,
                                  xaxis_title="JDs requiring skill", yaxis_title=None, coloraxis_showscale=False,
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, width="stretch", config={"displayModeBar":False})
            st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>Offer Acceptance</h4>",
                            unsafe_allow_html=True)
                # TODO: Requires schema addition. We don't have an 'Offer' model or a dedicated 'offer_status' field on Candidate/Application to track Accepted/Declined/Pending offers correctly.
                df2 = pd.DataFrame([{"Status":"Accepted","Count":28},{"Status":"Declined","Count":4},{"Status":"Pending","Count":6}])
                fig2 = px.pie(df2, values="Count", names="Status", hole=0.5,
                              color_discrete_sequence=["#10B981","#EF4444","#F59E0B"])
                fig2.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=230,
                                   showlegend=True, legend=dict(orientation="h",yanchor="bottom",y=-0.15,xanchor="center",x=0.5),
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, width="stretch", config={"displayModeBar":False})
        with col_r:
            with st.container(border=True):
                st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>Candidate Acquisition Sources</h4>",
                            unsafe_allow_html=True)
                
                if acquisition_sources_data:
                    df3 = pd.DataFrame(acquisition_sources_data)
                else:
                    df3 = pd.DataFrame([{"Source":"LinkedIn","Count":168},{"Source":"Referrals","Count":94},
                                        {"Source":"Careers Page","Count":62},{"Source":"Agencies","Count":28}])
                fig3 = px.pie(df3, values="Count", names="Source", hole=0.5,
                              color_discrete_sequence=["#4F46E5","#6366F1","#818CF8","#C7D2FE"])
                fig3.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=510,
                                   showlegend=True, legend=dict(orientation="h",yanchor="bottom",y=-0.15,xanchor="center",x=0.5),
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig3, width="stretch", config={"displayModeBar":False})

    with tab_recruiters:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>Recruiter Performance</h4>",
                        unsafe_allow_html=True)
            
            if recruiter_performance_data:
                df_rp = pd.DataFrame(recruiter_performance_data)
                recruiters = df_rp["Recruiter"].tolist()
                screens = df_rp["Screens Conducted"].tolist()
                hires = df_rp["Hires Advanced"].tolist()
            else:
                recruiters = ["Ava Morgan","Marcus Aurelius","Sophia Lin"]
                screens = [45,30,25]
                hires = [12,8,5]
                
            fig = go.Figure(data=[
                go.Bar(name="Screens Conducted", x=recruiters,
                       y=screens, marker_color="#818CF8"),
                go.Bar(name="Hires Advanced",    x=recruiters,
                       y=hires, marker_color="#10B981")
            ])
            fig.update_layout(barmode="group", margin=dict(l=20,r=20,t=20,b=20), height=450,
                              xaxis_title="Recruiter", yaxis_title="Count",
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width="stretch", config={"displayModeBar":False})
