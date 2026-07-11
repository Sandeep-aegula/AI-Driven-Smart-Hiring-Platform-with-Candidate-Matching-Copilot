"""
components/reports.py — HirePilot Reports Page
"""
import datetime
import io
import streamlit as st
import pandas as pd
from frontend.components import api_client


def render_reports() -> None:
    for k, v in [("reports_history",[
        {"filename":"Hiring_Report_Q2_2026.pdf","type":"Hiring Report","time":"3 hours ago"},
        {"filename":"Candidate_Roster_Jul_2026.csv","type":"Candidate Report","time":"2 days ago"},
        {"filename":"Interview_Logs_Jul_2026.xlsx","type":"Interview Report","time":"3 days ago"},
    ]), ("generated_report_type", None)]:
        if k not in st.session_state: st.session_state[k] = v

    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        📑 Reports
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        Generate and download recruitment metric reports
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

    templates = [
        {"name":"Hiring Report",    "desc":"Overview of hiring activities, pipelines and conversions", "icon":"fa-chart-pie"},
        {"name":"Candidate Report", "desc":"Detailed applicant qualifications, profiles, and match scores","icon":"fa-user-group"},
        {"name":"Interview Report", "desc":"Interview schedules, interviewer logs, and feedback notes",  "icon":"fa-calendar-check"},
        {"name":"Employee Report",  "desc":"Employee profiles, performance ratings, and skill indexes",   "icon":"fa-user-tie"},
    ]

    col_t, col_h = st.columns([1.1, 0.9])

    with col_t:
        st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                    "<i class='fa-solid fa-file-invoice' style='color:#6366F1;'></i> Report Templates</h4>",
                    unsafe_allow_html=True)
        for t in templates:
            with st.container(border=True):
                ci, cd = st.columns([1, 8])
                with ci:
                    st.markdown(f"""
                    <div style="width:44px;height:44px;border-radius:10px;background:#EEF2FF;
                                color:#6366F1;display:flex;align-items:center;
                                justify-content:center;font-size:18px;margin:4px auto;">
                        <i class="fa-solid {t['icon']}"></i></div>
                    """, unsafe_allow_html=True)
                with cd:
                    st.markdown(f"""
                    <div style="font-weight:800;color:#0F172A;font-size:1rem;">{t['name']}</div>
                    <div style="font-size:0.78rem;color:#64748B;margin:2px 0 10px 0;">{t['desc']}</div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Generate {t['name']}", key=f"gen_{t['name']}", type="secondary"):
                        st.session_state["generated_report_type"] = t["name"]
                        new_file = f"{t['name'].replace(' ','_')}_{datetime.datetime.now().strftime('%M%S')}.csv"
                        st.session_state["reports_history"].insert(0,{"filename":new_file,"type":t["name"],"time":"Just now"})
                        st.toast(f"{t['name']} compiled!", icon="📊"); st.rerun()
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    with col_h:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                        "<i class='fa-solid fa-clock-rotate-left' style='color:#6366F1;'></i> Report History</h4>",
                        unsafe_allow_html=True)
            html = "<div style='display:flex;flex-direction:column;gap:12px;max-height:420px;overflow-y:auto;'>"
            for r in st.session_state["reports_history"]:
                html += f"""
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
                            padding:12px 14px;display:flex;align-items:center;justify-content:space-between;">
                    <div>
                        <div style="font-weight:700;color:#0F172A;font-size:0.82rem;">
                            <i class="fa-solid fa-file-lines" style="color:#6366F1;margin-right:6px;"></i>{r['filename']}</div>
                        <div style="font-size:0.72rem;color:#94A3B8;margin-top:2px;">{r['type']} • Generated {r['time']}</div>
                    </div>
                    <div style="font-size:0.76rem;color:#4F46E5;font-weight:700;">📁 Saved</div>
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

    # ── Preview + Download ────────────────────────────────────────────────
    if st.session_state["generated_report_type"]:
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        rname = st.session_state["generated_report_type"]
        df = _get_report_data(rname)

        with st.container(border=True):
            st.markdown(f"<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                        f"<i class='fa-solid fa-magnifying-glass-chart' style='color:#6366F1;'></i>"
                        f" Report Preview: {rname}</h4>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)

            csv_buf   = df.to_csv(index=False).encode("utf-8")
            excel_buf = io.BytesIO()
            try:
                with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Report")
                excel_data = excel_buf.getvalue()
            except Exception:
                excel_data = csv_buf
            pdf_txt = (f"HIREPILOT REPORT: {rname.upper()}\n"
                       f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                       f"{'─'*60}\n\n{df.to_string()}\n\n{'─'*60}\nEnd of Report")
            pdf_buf = pdf_txt.encode("utf-8")

            da, db, dc, dd = st.columns([1,1,1,3])
            with da:
                st.download_button("📄 Download PDF", pdf_buf,
                                   f"{rname.replace(' ','_')}.pdf", "application/pdf", use_container_width=True)
            with db:
                st.download_button("📊 Download CSV", csv_buf,
                                   f"{rname.replace(' ','_')}.csv", "text/csv", use_container_width=True)
            with dc:
                st.download_button("📈 Download Excel", excel_data,
                                   f"{rname.replace(' ','_')}.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
            with dd:
                if st.button("Close Preview", use_container_width=True):
                    st.session_state["generated_report_type"] = None; st.rerun()


def _get_report_data(name: str) -> pd.DataFrame:
    if name == "Hiring Report":
        return pd.DataFrame([
            {"Month":"January","Applications":120,"Interviews":35,"Offers":6,"Hires":4},
            {"Month":"February","Applications":150,"Interviews":42,"Offers":8,"Hires":6},
            {"Month":"March","Applications":180,"Interviews":50,"Offers":10,"Hires":8},
            {"Month":"April","Applications":210,"Interviews":58,"Offers":11,"Hires":9},
        ])
    elif name == "Candidate Report":
        cands = api_client.get_candidates()
        if cands:
            return pd.DataFrame([{"Name":c.get("name"),"Role":c.get("current_title",""),"Experience":c.get("years_experience"),"Match%":c.get("match_score"),"Status":c.get("status")} for c in cands])
        return pd.DataFrame([{"Name":"Sarah Jenkins","Role":"ML Engineer","Experience":7,"Match%":91,"Status":"Approved"}])
    elif name == "Interview Report":
        ivs = api_client.get_interviews()
        if ivs:
            return pd.DataFrame([{"Candidate":i.get("candidate_name"),"Interviewer":i.get("interviewer"),"Stage":i.get("stage"),"Date":i.get("date"),"Status":i.get("status")} for i in ivs])
        return pd.DataFrame([{"Candidate":"Sarah Jenkins","Interviewer":"Ava Morgan","Stage":"Technical","Date":"2026-07-11","Status":"Scheduled"}])
    elif name == "Employee Report":
        emps = api_client.get_employees()
        if emps:
            return pd.DataFrame([{"Name":e.get("name"),"Department":e.get("department"),"Role":e.get("role"),"Manager":e.get("manager"),"Score":e.get("performance_score")} for e in emps])
        return pd.DataFrame([{"Name":"Alice Johnson","Department":"Engineering","Role":"Lead Frontend Eng","Manager":"Marcus Aurelius","Score":92}])
    return pd.DataFrame()
