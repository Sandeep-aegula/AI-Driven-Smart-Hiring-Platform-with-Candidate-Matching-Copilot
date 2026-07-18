"""
components/resume_parser.py — HirePilot Resume Parser Page
"""
import os
import streamlit as st
from frontend.components import api_client
from frontend.services.cache import get_uploads_cached, invalidate_uploads, invalidate_candidates


def render_resume_parser() -> None:
    if "selected_resume_id" not in st.session_state:
        st.session_state["selected_resume_id"] = None

    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        📄 Resume Parser
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        Upload and parse candidate resumes with Ollama AI
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

    uploads_list = get_uploads_cached()

    if st.session_state["selected_resume_id"] is None and uploads_list:
        st.session_state["selected_resume_id"] = uploads_list[0]["id"]

    # ── Top Section ───────────────────────────────────────────────────────
    col_left, col_right = st.columns([1.1, 0.9])

    with col_left:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 6px 0;'>"
                        "<i class='fa-solid fa-cloud-arrow-up' style='color:#6366F1;'></i>"
                        " Drag &amp; Drop Resumes</h4>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:0.82rem;color:#64748B;margin-bottom:15px;'>"
                        "Supports PDF, DOCX • Bulk Upload enabled</p>", unsafe_allow_html=True)

            uploaded_files = st.file_uploader(
                "Select files", type=["pdf", "docx"],
                accept_multiple_files=True,
                label_visibility="collapsed",
                key="bulk_resume_uploader"
            )

            if uploaded_files:
                progress_bar = st.progress(0)
                status_text  = st.empty()

                if st.button("Parse Resumes with Ollama AI", type="primary", use_container_width=True):
                    success = 0
                    for idx, file in enumerate(uploaded_files):
                        status_text.markdown(f"AI parsing: *{file.name}*…")
                        file_bytes = file.read()

                        # Save local copy
                        upload_dir = os.path.join(
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads"
                        )
                        os.makedirs(upload_dir, exist_ok=True)
                        with open(os.path.join(upload_dir, file.name), "wb") as f:
                            f.write(file_bytes)

                        res = api_client.upload_resume(file_bytes, file.name)
                        if res:
                            success += 1
                            st.toast(f"Parsed {file.name}!", icon="✅")
                        else:
                            st.error(f"Failed: {file.name}")

                        progress_bar.progress(int(((idx+1)/len(uploaded_files))*100))

                    invalidate_uploads()
                    invalidate_candidates()
                    status_text.markdown(f"### 🎉 Parsed {success}/{len(uploaded_files)} resume(s)!")
                    st.session_state["selected_resume_id"] = None
                    st.rerun()

            st.markdown("**Or paste resume text**")
            pasted_resume_text = st.text_area(
                "Resume text",
                height=180,
                placeholder="Paste the candidate's full resume text here...",
                key="pasted_resume_text",
            )
            if st.button("Parse pasted resume", type="primary", width="stretch"):
                if not pasted_resume_text.strip():
                    st.error("Paste resume text before parsing.")
                else:
                    with st.spinner("Parsing resume text with Ollama AI..."):
                        result = api_client.parse_resume_text(pasted_resume_text)
                    if result:
                        invalidate_uploads()
                        invalidate_candidates()
                        st.session_state["selected_resume_id"] = result["id"]
                        st.success("Resume parsed successfully.")
                        st.rerun()
                    else:
                        st.error("Unable to parse the pasted resume text.")

    with col_right:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                        "<i class='fa-solid fa-clock-rotate-left' style='color:#6366F1;'></i>"
                        " Upload History</h4>", unsafe_allow_html=True)
            if uploads_list:
                upload_map = {
                    f"📄 {u.get('filename','resume')} ({u.get('name') or 'New Applicant'})": u["id"]
                    for u in uploads_list
                }
                sel = st.selectbox("Select File", list(upload_map.keys()), index=0,
                                   key="upload_file_sel")
                st.session_state["selected_resume_id"] = upload_map[sel]
            else:
                st.markdown("<p style='color:#64748B;font-size:0.85rem;'>No uploads yet.</p>",
                            unsafe_allow_html=True)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Split-pane Preview ────────────────────────────────────────────────
    selected = None
    if st.session_state["selected_resume_id"] and uploads_list:
        selected = next((u for u in uploads_list
                         if u["id"] == st.session_state["selected_resume_id"]), None)

    if selected:
        cb_left, cb_right = st.columns(2)

        with cb_left:
            with st.container(border=True):
                st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                            "<i class='fa-solid fa-file-pdf' style='color:#EF4444;'></i>"
                            " Resume Preview (Raw Text)</h4>", unsafe_allow_html=True)
                st.text_area("Raw text", value=selected.get("extracted_text","No text available."),
                             height=450, disabled=True, label_visibility="collapsed")

        with cb_right:
            parsed = selected.get("parsed_json") or selected
            with st.container(border=True):
                st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                            "<i class='fa-solid fa-wand-magic-sparkles' style='color:#6366F1;'></i>"
                            " Parsed Information</h4>", unsafe_allow_html=True)

                tabs = st.tabs(["👤 Identity","⚡ Skills","💼 Career","🎓 Education","🏆 Others"])

                with tabs[0]:
                    for lbl, key in [("Name","name"),("Email","email"),("Phone","phone")]:
                        st.markdown(f"**{lbl}:** {parsed.get(key) or 'N/A'}")
                    for lbl, key in [("LinkedIn", "linkedin"), ("GitHub", "github"), ("Portfolio", "portfolio")]:
                        url = parsed.get(key) or ""
                        if url.startswith(("https://", "http://")):
                            st.link_button(f"{lbl} profile", url, width="content")
                        else:
                            st.markdown(f"**{lbl}:** N/A")

                with tabs[1]:
                    skills = parsed.get("skills",[])
                    if skills:
                        st.pills(
                            "Skills",
                            skills,
                            selection_mode="multi",
                            default=skills,
                            disabled=True,
                            label_visibility="collapsed",
                            width="stretch",
                            key=f"parsed_skills_{selected['id']}",
                        )
                    else:
                        st.write("No skills extracted.")

                with tabs[2]:
                    st.markdown("**Work Experience:**")
                    for e in parsed.get("experience",[]): st.markdown(f"- {e}")
                    st.markdown("**Projects:**")
                    for p in parsed.get("projects",[]): st.markdown(f"- {p}")

                with tabs[3]:
                    st.markdown("**Education:**")
                    for e in parsed.get("education",[]): st.markdown(f"- {e}")
                    st.markdown("**Certifications:**")
                    for c in parsed.get("certifications",[]): st.markdown(f"- {c}")

                with tabs[4]:
                    st.markdown("**Languages:**")
                    for l in parsed.get("languages",[]): st.markdown(f"- {l}")
                    st.markdown("**Achievements:**")
                    for a in parsed.get("achievements",[]): st.markdown(f"- {a}")

    # ── Recent Uploads Table ──────────────────────────────────────────────
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                    "<i class='fa-solid fa-list' style='color:#6366F1;'></i> Recent Uploads</h4>",
                    unsafe_allow_html=True)
        if uploads_list:
            rows = ""
            for u in uploads_list[:6]:
                rows += f"""
                <tr style="border-bottom:1px solid #F1F5F9;">
                    <td style="padding:10px;font-weight:700;color:#4F46E5;">{u.get('filename')}</td>
                    <td style="padding:10px;color:#0F172A;font-weight:600;">{u.get('name') or 'N/A'}</td>
                    <td style="padding:10px;color:#475569;">{u.get('email') or 'N/A'}</td>
                    <td style="padding:10px;color:#475569;">{u.get('phone') or 'N/A'}</td>
                    <td style="padding:10px;">
                        <span class="badge-strong" style="background:#ECFDF5;color:#047857;font-size:0.72rem;padding:2px 10px;">
                            {u.get('status','Parsed')}
                        </span>
                    </td>
                </tr>"""
            st.markdown(f"""
            <table class="custom-table">
                <thead>
                    <tr style="background:#F8FAFC;border-bottom:2px solid #E2E8F0;">
                        <th style="padding:10px;">Filename</th>
                        <th style="padding:10px;">Candidate</th>
                        <th style="padding:10px;">Email</th>
                        <th style="padding:10px;">Phone</th>
                        <th style="padding:10px;">Status</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            """, unsafe_allow_html=True)
        else:
            st.write("No uploads yet.")
