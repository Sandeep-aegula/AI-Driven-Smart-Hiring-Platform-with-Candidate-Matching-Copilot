"""
components/candidates.py — HirePilot Candidate Management Page
===============================================================
Renders the Candidates list with split-pane profile drawer.
Navigation to AI Screening via session_state (no st.switch_page).
"""

import datetime
import streamlit as st
from frontend.components import api_client


def render_candidates() -> None:
    if "selected_cand_id" not in st.session_state:
        st.session_state["selected_cand_id"] = None

    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        👥 Candidate Profiles
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        Manage and screen applicants
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

    # ── Filters ───────────────────────────────────────────────────────────
    cs, cst, ce, csk = st.columns([3.5, 2.1, 2.1, 2.1])
    with cs:  search    = st.text_input("Search", placeholder="Search by name, title…", label_visibility="collapsed")
    with cst: status_f  = st.selectbox("Status",  ["All","Applied","Shortlisted","Interview Scheduled","Approved","Rejected"], label_visibility="collapsed")
    with ce:  exp_f     = st.selectbox("Exp",     ["All","Junior (0-2 Yrs)","Mid-level (3-5 Yrs)","Senior (6+ Yrs)"], label_visibility="collapsed")
    with csk: skill_f   = st.selectbox("Skill",   ["All","Python","SQL","FastAPI","React","Docker","Machine Learning"], label_visibility="collapsed")

    cands = api_client.get_candidates(search=search, status=status_f, skill=skill_f)
    if "Junior"    in exp_f: cands = [c for c in cands if c.get("years_experience",0) <= 2]
    elif "Mid"     in exp_f: cands = [c for c in cands if 3 <= c.get("years_experience",0) <= 5]
    elif "Senior"  in exp_f: cands = [c for c in cands if c.get("years_experience",0) >= 6]

    # ── Layout ────────────────────────────────────────────────────────────
    drawer_open = st.session_state["selected_cand_id"] is not None
    if drawer_open:
        list_col, drawer_col = st.columns([1.1, 0.9])
    else:
        list_col  = st.container()
        drawer_col = None

    # ── List ──────────────────────────────────────────────────────────────
    with list_col:
        if not cands:
            st.markdown("<p style='text-align:center;color:#64748B;padding:40px 0;'>No candidates match the criteria.</p>",
                        unsafe_allow_html=True)
        else:
            for c in cands:
                mc   = "#10B981" if c.get("match_score",0) >= 85 else ("#F59E0B" if c.get("match_score",0) >= 70 else "#EF4444")
                tags = "".join(f'<span class="tag">{s.get("name") if isinstance(s,dict) else s}</span>'
                               for s in c.get("skills",[])[:4])
                if len(c.get("skills",[])) > 4:
                    tags += f'<span class="tag">+{len(c.get("skills",[]))-4} more</span>'

                c_det  = api_client.get_candidate(c["id"]) or {}
                resumes = c_det.get("resumes", [])
                has_res = len(resumes) > 0
                res_lbl = f"📄 {resumes[-1]['filename']}" if has_res else "❌ No Resume Uploaded"

                with st.container(border=True):
                    ca, cb = st.columns([1, 6])
                    with ca:
                        ini = "".join(p[0] for p in c.get("name","C").split()[:2])
                        st.markdown(f"""
                        <div style="width:44px;height:44px;border-radius:50%;background:#EEF2FF;
                                    border:1.5px solid #6366F1;display:flex;align-items:center;
                                    justify-content:center;font-weight:800;color:#6366F1;
                                    font-size:14px;margin:5px auto;">{ini}</div>
                        """, unsafe_allow_html=True)
                    with cb:
                        st.markdown(f"""
                        <div>
                            <div style="display:flex;align-items:center;gap:8px;">
                                <span style="font-weight:800;font-size:1.1rem;color:#0F172A;">{c.get('name')}</span>
                                <span style="background:#ECFDF5;color:#047857;font-size:0.65rem;
                                             padding:2px 10px;border-radius:9999px;font-weight:600;">{c.get('status')}</span>
                                <span style="background:{mc}10;color:{mc};font-size:0.65rem;
                                             padding:2px 10px;border-radius:9999px;font-weight:600;">{c.get('match_score',0)}% Match</span>
                            </div>
                            <p style="font-size:0.8rem;color:#64748B;margin:2px 0 6px 0;">
                                {c.get('current_title') or 'Applicant'} • {c.get('years_experience')} Yrs • {c.get('location')}
                            </p>
                            <div style="font-size:0.72rem;color:#475569;margin-bottom:8px;">
                                <i class="fa-solid fa-file-contract"></i> <strong>Resume:</strong> {res_lbl}
                            </div>
                            <div>{tags}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                    bc = st.columns(5)
                    with bc[0]:
                        if st.button("View Profile", key=f"vp_{c['id']}", use_container_width=True):
                            st.session_state["selected_cand_id"] = c["id"]; st.rerun()
                    with bc[1]:
                        if st.button("AI Summary", key=f"as_{c['id']}", use_container_width=True, type="secondary"):
                            st.session_state[f"ai_sum_open_{c['id']}"] = not st.session_state.get(f"ai_sum_open_{c['id']}", False)
                            st.rerun()
                    with bc[2]:
                        if st.button("Compare", key=f"cmp_{c['id']}", use_container_width=True, type="secondary"):
                            st.session_state["selected_eval_cand_id"] = c["id"]
                            st.session_state["current_page"] = "AI Screening"
                            st.rerun()
                    with bc[3]:
                        if st.button("Interview", key=f"iv_{c['id']}", use_container_width=True, type="secondary"):
                            r = api_client.update_candidate_status(c["id"], "Interview Scheduled")
                            if r: st.toast("Status updated!", icon="📅"); st.rerun()
                    with bc[4]:
                        if st.button("Resume", key=f"rv_{c['id']}", use_container_width=True, type="secondary"):
                            st.session_state[f"res_prev_{c['id']}"] = not st.session_state.get(f"res_prev_{c['id']}", False)
                            st.rerun()

                if st.session_state.get(f"ai_sum_open_{c['id']}", False):
                    with st.container(border=True):
                        st.markdown("**🤖 AI Summary:**")
                        st.write(c.get("summary") or "AI summary parsed successfully.")

                if st.session_state.get(f"res_prev_{c['id']}", False):
                    with st.container(border=True):
                        st.markdown("**📄 Parsed Resume Details:**")
                        if has_res:
                            r = resumes[-1]
                            st.markdown(f"**Education:** {', '.join(r.get('education',[]))}")
                            st.markdown(f"**Certifications:** {', '.join(r.get('certifications',[]))}")
                            st.markdown(f"**Experience:** {', '.join(r.get('experience',[]))}")
                        else:
                            st.write("No parsed resume available.")

                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # ── Profile Drawer ────────────────────────────────────────────────────
    if drawer_col and st.session_state["selected_cand_id"]:
        cand    = api_client.get_candidate(st.session_state["selected_cand_id"])
        resumes = cand.get("resumes", [])
        has_res = len(resumes) > 0

        with drawer_col:
            with st.container(border=True):
                hc1, hc2 = st.columns([8, 2])
                with hc1:
                    st.markdown("<h3><i class='fa-solid fa-user-tie' style='color:#6366F1;'></i> Profile Details</h3>",
                                unsafe_allow_html=True)
                with hc2:
                    if st.button("✕ Close", key="close_drawer", use_container_width=True):
                        st.session_state["selected_cand_id"] = None; st.rerun()

                st.markdown(f"""
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
                            padding:16px;margin-bottom:15px;">
                    <h4 style="margin:0;color:#0F172A;font-weight:800;">{cand.get('name')}</h4>
                    <p style="margin:2px 0 0;font-size:0.8rem;color:#4F46E5;font-weight:600;">
                        {cand.get('current_title') or 'Applicant'}</p>
                    <div style="font-size:0.75rem;color:#64748B;margin-top:6px;">
                        Status: <strong>{cand.get('status')}</strong></div>
                </div>
                """, unsafe_allow_html=True)

                t1, t2, t3, t4 = st.tabs(["📝 Overview","📄 Resume","⏳ Timeline","💬 Notes"])

                with t1:
                    st.markdown("**Contact:**")
                    st.markdown(f"- **Email:** {cand.get('email')}")
                    st.markdown(f"- **Phone:** {cand.get('phone') or 'N/A'}")
                    st.markdown(f"- **Location:** {cand.get('location') or 'Remote'}")
                    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                    li = f"[LinkedIn]({cand.get('linkedin')})" if cand.get("linkedin") else "LinkedIn (Not linked)"
                    gh = f"[GitHub]({cand.get('github')})"   if cand.get("github")   else "GitHub (Not linked)"
                    st.markdown(f"- <i class='fa-brands fa-linkedin' style='color:#0077b5;'></i> {li}", unsafe_allow_html=True)
                    st.markdown(f"- <i class='fa-brands fa-github'></i> {gh}", unsafe_allow_html=True)
                    if has_res:
                        r = resumes[-1]
                        st.markdown("**Education:**")
                        for e in r.get("education",[]): st.markdown(f"- {e}")
                        st.markdown("**Certifications:**")
                        for cert in r.get("certifications",[]): st.markdown(f"- {cert}")

                with t2:
                    if has_res:
                        r = resumes[-1]
                        st.markdown("**Experience:**")
                        for e in r.get("experience",[]): st.markdown(f"- {e}")
                        st.markdown("**Projects:**")
                        for p in r.get("projects",[]): st.markdown(f"- {p}")
                        with st.expander("Raw extracted text"):
                            st.text_area("", value=r.get("extracted_text",""), height=200, disabled=True, label_visibility="collapsed")
                    else:
                        st.write("No resume uploaded yet.")

                with t3:
                    timeline = [{"title":"Application Started","desc":"Profile registered.","time":cand.get("created_at")}]
                    for note in cand.get("notes",[]):
                        timeline.append({"title":f"Note by {note.get('author')}","desc":note.get("note"),"time":note.get("created_at")})
                    timeline.sort(key=lambda t: t.get("time",""), reverse=True)
                    html = "<div style='display:flex;flex-direction:column;gap:14px;margin-top:10px;'>"
                    for idx, ev in enumerate(timeline):
                        ts = datetime.datetime.fromisoformat(ev["time"]).strftime("%b %d, %H:%M") if ev.get("time") else "Just now"
                        html += f"""
                        <div style="display:flex;gap:10px;">
                            <div style="display:flex;flex-direction:column;align-items:center;">
                                <div style="width:18px;height:18px;border-radius:50%;background:#6366F1;border:3px solid #EEF2FF;"></div>
                                {"<div style='width:2px;flex-grow:1;background:#E2E8F0;'></div>" if idx < len(timeline)-1 else ""}
                            </div>
                            <div style="padding-bottom:10px;">
                                <div style="font-weight:700;color:#0F172A;font-size:0.8rem;">{ev['title']}</div>
                                <div style="font-size:0.76rem;color:#64748B;">{ev['desc']}</div>
                                <div style="font-size:0.68rem;color:#94A3B8;font-weight:500;">{ts}</div>
                            </div>
                        </div>"""
                    html += "</div>"
                    st.markdown(html, unsafe_allow_html=True)

                with t4:
                    new_note = st.text_area("Write note…", placeholder="Enter review remarks…", label_visibility="collapsed", key="drawer_note")
                    if st.button("Save Note", type="primary", use_container_width=True):
                        if new_note.strip():
                            r = api_client.add_candidate_note(cand["id"], new_note.strip())
                            if r: st.toast("Note saved!", icon="📝"); st.rerun()
                    notes = cand.get("notes", [])
                    if notes:
                        html = "<div style='display:flex;flex-direction:column;gap:10px;margin-top:15px;max-height:200px;overflow-y:auto;'>"
                        for n in notes:
                            ts = datetime.datetime.fromisoformat(n["created_at"]).strftime("%b %d, %H:%M") if n.get("created_at") else "Just now"
                            html += f"""
                            <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:10px 12px;">
                                <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:#64748B;font-weight:600;margin-bottom:4px;">
                                    <span>{n.get('author','Recruiter')}</span><span>{ts}</span></div>
                                <p style="margin:0;font-size:0.78rem;color:#334155;">{n.get('note')}</p>
                            </div>"""
                        html += "</div>"
                        st.markdown(html, unsafe_allow_html=True)
