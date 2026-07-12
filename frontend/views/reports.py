import streamlit as st
import os
import sys
import datetime
import pandas as pd
import io

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.components import api_client
from frontend.services.app_state import AppState
from frontend.components.page_utils import setup_page, render_sidebar_footer

# Page Config
st.set_page_config(
    page_title="Reports - HirePilot",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

setup_page("Reports", "Generate and download recruitment metrics reports", page_key=__file__)

# State initialization
if "reports_history" not in st.session_state:
    st.session_state.reports_history = [
        {"filename": "Hiring_Report_Q2_2026.pdf", "type": "Hiring Report", "time": "3 hours ago"},
        {"filename": "Candidate_Roster_Jul_2026.csv", "type": "Candidate Report", "time": "2 days ago"},
        {"filename": "Interview_Logs_Jul_2026.xlsx", "type": "Interview Report", "time": "3 days ago"}
    ]
if "generated_report_type" not in st.session_state:
    st.session_state.generated_report_type = None

# Report templates metadata
templates = [
    {"name": "Hiring Report", "desc": "Overview of hiring activities, pipelines and conversions", "icon": "fa-chart-pie"},
    {"name": "Candidate Report", "desc": "Detailed applicant qualifications, profiles, and match scores", "icon": "fa-user-group"},
    {"name": "Interview Report", "desc": "Interview schedules, interviewer logs, and feedback notes", "icon": "fa-calendar-check"},
    {"name": "Employee Report", "desc": "Employee profiles, performance ratings, and skill indexes", "icon": "fa-user-tie"}
]

# Helper to generate DataFrames
def get_report_data(report_name):
    if report_name == "Hiring Report":
        return pd.DataFrame([
            {"Month": "January", "Applications Received": 120, "Interviews Screened": 35, "Offers Extended": 6, "Hires Confirmed": 4},
            {"Month": "February", "Applications Received": 150, "Interviews Screened": 42, "Offers Extended": 8, "Hires Confirmed": 6},
            {"Month": "March", "Applications Received": 180, "Interviews Screened": 50, "Offers Extended": 10, "Hires Confirmed": 8},
            {"Month": "April", "Applications Received": 210, "Interviews Screened": 58, "Offers Extended": 11, "Hires Confirmed": 9}
        ])
    elif report_name == "Candidate Report":
        candidates = api_client.get_candidates()
        if candidates:
            return pd.DataFrame([
                {"Candidate Name": c.get("name"), "Role Title": c.get("current_title", "Applicant"), "Experience (Yrs)": c.get("years_experience"), "AI Match %": c.get("match_score"), "Current Status": c.get("status")}
                for c in candidates
            ])
        else:
            return pd.DataFrame([
                {"Candidate Name": "Sarah Jenkins", "Role Title": "Senior Python & ML Engineer", "Experience (Yrs)": 7, "AI Match %": 91, "Current Status": "Approved"},
                {"Candidate Name": "David Chen", "Role Title": "Data Analyst", "Experience (Yrs)": 4, "AI Match %": 85, "Current Status": "Shortlisted"}
            ])
    elif report_name == "Interview Report":
        interviews = api_client.get_interviews()
        if interviews:
            return pd.DataFrame([
                {"Candidate Name": i.get("candidate_name"), "Interviewer": i.get("interviewer"), "Stage": i.get("stage"), "Date Scheduled": i.get("date"), "Time": i.get("time"), "Status": i.get("status")}
                for i in interviews
            ])
        else:
            return pd.DataFrame([
                {"Candidate Name": "Sarah Jenkins", "Interviewer": "Ava Morgan", "Stage": "Technical Assessment", "Date Scheduled": "2026-07-11", "Time": "10:00", "Status": "Scheduled"},
                {"Candidate Name": "David Chen", "Interviewer": "Ava Morgan", "Stage": "HR Culture Fit", "Date Scheduled": "2026-07-11", "Time": "11:30", "Status": "Scheduled"}
            ])
    elif report_name == "Employee Report":
        employees = api_client.get_employees()
        if employees:
            return pd.DataFrame([
                {"Employee Name": e.get("name"), "Department": e.get("department"), "Current Role": e.get("role"), "Direct Manager": e.get("manager"), "Performance score": e.get("performance_score")}
                for e in employees
            ])
        else:
            return pd.DataFrame([
                {"Employee Name": "Alice Johnson", "Department": "Engineering", "Current Role": "Lead Frontend Engineer", "Direct Manager": "Marcus Aurelius", "Performance score": 92},
                {"Employee Name": "Bob Chen", "Department": "Engineering", "Current Role": "Senior ML Engineer", "Direct Manager": "Ava Morgan", "Performance score": 88}
            ])
    return pd.DataFrame()

# Main Layout
col_templates, col_recent = st.columns([1.1, 0.9])

with col_templates:
    st.markdown("#### <i class='fa-solid fa-file-invoice' style='color:#6366F1;'></i> Report Templates", unsafe_allow_html=True)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    for t in templates:
        with st.container(border=True):
            col_icon, col_details = st.columns([1, 8])
            with col_icon:
                st.markdown(f"""
                <div style="width: 44px; height: 44px; border-radius: 10px; background-color: #EEF2FF; color: #6366F1; display: flex; align-items: center; justify-content: center; font-size: 18px; margin: 5px auto;">
                    <i class="fa-solid {t['icon']}"></i>
                </div>
                """, unsafe_allow_html=True)
            with col_details:
                st.markdown(f"""
                <div style="font-weight: 800; color: #0F172A; font-size: 1.05rem;">{t['name']}</div>
                <div style="font-size: 0.8rem; color: #64748B; margin: 2px 0 10px 0;">{t['desc']}</div>
                """, unsafe_allow_html=True)
                
                # Button Trigger to compile report
                if st.button(f"Generate {t['name']}", key=f"gen_btn_{t['name']}", type="secondary"):
                    st.session_state.generated_report_type = t["name"]
                    
                    # Append record to history timeline
                    new_file = f"{t['name'].replace(' ', '_')}_{datetime.datetime.now().strftime('%M%S')}.csv"
                    st.session_state.reports_history.insert(0, {
                        "filename": new_file,
                        "type": t["name"],
                        "time": "Just now"
                    })
                    st.toast(f"{t['name']} successfully compiled!", icon="📊")
                    st.rerun()
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

with col_recent:
    with st.container(border=True):
        st.markdown("#### <i class='fa-solid fa-clock-rotate-left' style='color:#6366F1;'></i> Report History", unsafe_allow_html=True)
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        recent_html = "<div style='display: flex; flex-direction: column; gap: 12px; max-height: 380px; overflow-y: auto;'>"
        for r in st.session_state.reports_history:
            recent_html += f"""
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 14px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-weight: 700; color: #0F172A; font-size: 0.82rem;"><i class="fa-solid fa-file-lines" style="color: #6366F1; margin-right: 6px;"></i> {r['filename']}</div>
                    <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 2px;">{r['type']} • Generated {r['time']}</div>
                </div>
                <div style="font-size: 0.76rem; color:#4F46E5; font-weight:700;">📁 Saved</div>
            </div>
            """
        recent_html += "</div>"
        st.markdown(recent_html, unsafe_allow_html=True)

# Bottom preview & download block
if st.session_state.generated_report_type:
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    report_name = st.session_state.generated_report_type
    df = get_report_data(report_name)
    
    with st.container(border=True):
        st.markdown(f"#### <i class='fa-solid fa-magnifying-glass-chart' style='color:#6366F1;'></i> Report Preview: {report_name}", unsafe_allow_html=True)
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        st.dataframe(df, use_container_width=True)
        
        # Download Buffers
        csv_buffer = df.to_csv(index=False).encode('utf-8')
        
        # Safe Excel Buffer
        excel_buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Report')
            excel_data = excel_buffer.getvalue()
        except Exception:
            excel_data = csv_buffer  # fallback to csv bytes
            
        # PDF Text Buffer
        pdf_text = f"""HIREPILOT ANALYSIS REPORT: {report_name.upper()}
Generated At: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
--------------------------------------------------

{df.to_string()}

--------------------------------------------------
End of Report
"""
        pdf_buffer = pdf_text.encode('utf-8')
        
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        
        # Download Buttons Grid
        d_col1, d_col2, d_col3, d_col_close = st.columns([1, 1, 1, 3])
        with d_col1:
            st.download_button(
                label="📄 Download PDF",
                data=pdf_buffer,
                file_name=f"{report_name.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with d_col2:
            st.download_button(
                label="📊 Download CSV",
                data=csv_buffer,
                file_name=f"{report_name.replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with d_col3:
            st.download_button(
                label="📈 Download Excel",
                data=excel_data,
                file_name=f"{report_name.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with d_col_close:
            if st.button("Close Preview", use_container_width=True):
                st.session_state.generated_report_type = None
                st.rerun()
