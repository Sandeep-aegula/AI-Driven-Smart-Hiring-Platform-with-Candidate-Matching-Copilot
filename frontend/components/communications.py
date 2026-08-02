from __future__ import annotations

import streamlit as st
from frontend.components import api_client
from frontend.services.cache import get_candidates_cached, get_jobs_cached
from frontend.components.file_uploader import file_uploader_simple

EMAIL_TYPE_OPTIONS = [
    "Interview Invitation",
    "Offer Letter",
    "Rejection",
    "Hold Notification",
    "Next Round Invitation",
]


def fetch_pending_communications():
    """Fetch pending communications via the shared API client."""
    try:
        return api_client.get_pending_communications()
    except Exception as e:
        st.error(f"Error fetching pending communications: {e}")
        return []


def fetch_communications_history(page: int = 1, page_size: int = 25, status: str = None):
    """Fetch communications history from the database Communication table."""
    try:
        return api_client.get_communications_history_db(page=page, page_size=page_size, status=status)
    except Exception as e:
        st.error(f"Error fetching history: {e}")
        return {"items": [], "total": 0}


def _display_send_result(result: dict | None) -> bool:
    if not result:
        st.error("Email service failed to send the message.")
        return False

    sent = int(result.get("sent", 0) or 0)
    failed = int(result.get("failed", 0) or 0)
    message = result.get("message") or result.get("error_message") or "Email service failed to send the message."

    if sent > 0 and failed == 0 and result.get("success"):
        st.success(message)
        return True

    if sent > 0 and failed > 0:
        st.warning(f"{sent} emails sent successfully. {failed} emails failed.")
        return True

    st.error(message)
    return False


def send_bulk_communications(communication_ids: list, subject: str, body: str, sender_name: str = "Recruitment Team"):
    """Send bulk emails to selected candidates via the shared API client."""
    try:
        return api_client.send_bulk_communications(
            communication_ids=communication_ids,
            subject=subject,
            body=body,
            sender_name=sender_name,
        )
    except Exception as e:
        st.error(f"Error sending bulk emails: {e}")
        return None


def _render_pending_queue():
    st.markdown("### Pending Interview Communications")
    st.write("Scheduled interviews awaiting draft generation, review, and sending.")
    st.caption("Generate and manage one draft per communication record. Drafts remain in MySQL until sent or cancelled.")

    pending = fetch_pending_communications()
    if not pending:
        st.info("No pending interview communications found.")
        return

    if "comm_selected_ids" not in st.session_state:
        st.session_state.comm_selected_ids = []

    current_selection = set(st.session_state.comm_selected_ids)
    select_all = st.checkbox("Select All", value=len(current_selection) == len(pending) and len(pending) > 0, key="comm_select_all")
    if select_all:
        st.session_state.comm_selected_ids = [item.get("id") for item in pending]
        current_selection = set(st.session_state.comm_selected_ids)

    bulk_left, bulk_right = st.columns([2, 1])
    with bulk_left:
        if st.button("Clear Selection", width="stretch"):
            st.session_state.comm_selected_ids = []
            st.rerun()
    with bulk_right:
        generate_label = f"Generate Drafts ({len(current_selection)})" if current_selection else "Generate Drafts"
        generate_bulk = st.button(generate_label, type="primary", width="stretch", disabled=not current_selection)

    if generate_bulk and current_selection:
        with st.spinner("Generating personalized interview drafts..."):
            result = api_client.generate_bulk_interview_drafts(sorted(current_selection))
        if result:
            st.success(result.get("message") or "Interview drafts generated successfully.")
            for failure in result.get("results", []):
                if failure.get("status") == "failed":
                    st.warning(f"{failure.get('communication_id')}: {failure.get('error_message')}")
            api_client.clear_interviews_cache()
            st.rerun()
        else:
            st.error("Draft generation failed.")

    st.markdown(f"**{len(pending)} communications awaiting action**")
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    for item in pending:
        comm_id = item.get("id")
        is_selected = comm_id in current_selection
        draft_open = st.session_state.get(f"comm_preview_{comm_id}", False)
        edit_open = st.session_state.get(f"comm_edit_{comm_id}", False)
        regen_open = st.session_state.get(f"comm_regen_{comm_id}", False)

        with st.container(border=True):
            row_left, row_right = st.columns([0.15, 0.85])
            with row_left:
                if st.checkbox("Select", value=is_selected, key=f"comm_select_{comm_id}", label_visibility="collapsed"):
                    if comm_id not in st.session_state.comm_selected_ids:
                        st.session_state.comm_selected_ids.append(comm_id)
                elif comm_id in st.session_state.comm_selected_ids:
                    st.session_state.comm_selected_ids.remove(comm_id)

            with row_right:
                st.markdown(f"**{item.get('candidate_name')}**  ")
                st.caption(
                    f"{item.get('job_title') or 'Unknown role'} | Round {item.get('round') or 'N/A'} | {item.get('interview_date') or 'N/A'} {item.get('interview_time') or ''} | {item.get('interview_mode') or 'N/A'} | Status: {item.get('status') or 'pending'}"
                )
                if item.get("invitation_email_status"):
                    st.caption(f"Interview status: {item.get('invitation_email_status')}")

                action_cols = st.columns(5)
                with action_cols[0]:
                    if st.button("Generate Draft", key=f"gen_{comm_id}", width="stretch"):
                        with st.spinner("Generating draft..."):
                            draft = api_client.generate_interview_draft(comm_id, regenerate=False)
                        if draft:
                            st.success("Interview invitation draft generated successfully.")
                            st.session_state[f"comm_preview_{comm_id}"] = True
                            st.session_state[f"comm_edit_{comm_id}"] = False
                            st.session_state[f"comm_regen_{comm_id}"] = False
                            api_client.clear_interviews_cache()
                            st.rerun()
                        else:
                            st.error("Failed to generate draft.")

                with action_cols[1]:
                    if st.button("Preview", key=f"prev_{comm_id}", width="stretch"):
                        st.session_state[f"comm_preview_{comm_id}"] = not draft_open
                        st.rerun()

                with action_cols[2]:
                    if st.button("Edit Draft", key=f"edit_{comm_id}", width="stretch"):
                        st.session_state[f"comm_edit_{comm_id}"] = True
                        st.session_state[f"comm_preview_{comm_id}"] = True
                        st.rerun()

                with action_cols[3]:
                    if st.button("Regenerate", key=f"regen_{comm_id}", width="stretch"):
                        st.session_state[f"comm_regen_{comm_id}"] = True
                        st.rerun()

                with action_cols[4]:
                    if st.button("Send", key=f"send_{comm_id}", width="stretch"):
                        result = api_client.send_interview_draft(comm_id)
                        if result and result.get("success"):
                            st.success(result.get("message") or "Interview invitation sent successfully.")
                            st.session_state.pop(f"comm_preview_{comm_id}", None)
                            st.session_state.pop(f"comm_edit_{comm_id}", None)
                            st.session_state.pop(f"comm_regen_{comm_id}", None)
                            api_client.clear_interviews_cache()
                            st.rerun()
                        elif result:
                            st.error(result.get("message") or result.get("error_message") or "Failed to send interview invitation.")

                if regen_open:
                    st.warning("Regenerating will replace the current draft. Continue?")
                    regen_confirm, regen_cancel = st.columns(2)
                    with regen_confirm:
                        if st.button("Yes, regenerate", key=f"regen_yes_{comm_id}", type="primary", width="stretch"):
                            draft = api_client.generate_interview_draft(comm_id, regenerate=True)
                            if draft:
                                st.success("Interview invitation draft generated successfully.")
                                st.session_state[f"comm_preview_{comm_id}"] = True
                                st.session_state[f"comm_regen_{comm_id}"] = False
                                st.session_state[f"comm_edit_{comm_id}"] = False
                                api_client.clear_interviews_cache()
                                st.rerun()
                            else:
                                st.error("Failed to regenerate draft.")
                    with regen_cancel:
                        if st.button("Cancel", key=f"regen_no_{comm_id}", width="stretch"):
                            st.session_state[f"comm_regen_{comm_id}"] = False
                            st.rerun()

                if item.get("status") == "draft" or draft_open or edit_open:
                    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                    if edit_open and item.get("status") == "draft":
                        edited_subject = st.text_input("Email Subject", value=item.get("subject") or "", key=f"subject_edit_{comm_id}")
                        edited_body = st.text_area("Email Body", value=item.get("message") or "", height=260, key=f"body_edit_{comm_id}")
                        save_col, cancel_col = st.columns(2)
                        with save_col:
                            if st.button("Save Draft", key=f"save_{comm_id}", type="primary", width="stretch"):
                                saved = api_client.save_interview_draft(comm_id, edited_subject, edited_body)
                                if saved:
                                    st.success("Draft saved.")
                                    st.session_state[f"comm_edit_{comm_id}"] = False
                                    st.session_state[f"comm_preview_{comm_id}"] = True
                                    api_client.clear_interviews_cache()
                                    st.rerun()
                                else:
                                    st.error("Failed to save draft.")
                        with cancel_col:
                            if st.button("Cancel Edit", key=f"cancel_edit_{comm_id}", width="stretch"):
                                st.session_state[f"comm_edit_{comm_id}"] = False
                                st.rerun()
                    else:
                        st.markdown(f"**Subject:** {item.get('subject') or ''}")
                        st.text_area(
                            "Email Body Preview",
                            value=item.get("message") or "",
                            height=220,
                            key=f"body_preview_{comm_id}",
                            disabled=True,
                            label_visibility="collapsed",
                        )

                if st.button("Cancel Communication", key=f"cancel_comm_{comm_id}", width="stretch"):
                    cancelled = api_client.cancel_interview_communication(comm_id)
                    if cancelled:
                        st.success("Communication cancelled.")
                        api_client.clear_interviews_cache()
                        st.rerun()
                    else:
                        st.error("Failed to cancel communication.")


def _render_history():
    st.markdown("### Sent & Draft History")
    query = st.text_input("Filter by candidate name, subject or email type")
    status = st.selectbox("Status", ["All", "Sent", "Draft", "Failed"], index=0)
    page = st.session_state.get("comm_history_page", 1)
    if st.button("Refresh History"):
        api_client.clear_candidates_cache()
        api_client.clear_interviews_cache()
        st.session_state["comm_history_page"] = 1
        st.rerun()

    history = api_client.get_communications_history(page=page, status=status if status != "All" else None, candidate_name=query)
    items = history.get("items", []) if history else []
    if not items:
        st.info("No communications records match the current filters.")
        return

    if status == "Failed":
        if st.button("Retry Failed", type="primary", width="stretch"):
            retry_ids = [item.get("id") for item in items]
            retry_result = api_client.send_bulk_communications(retry_ids, "", "", "Recruitment Team")
            if retry_result:
                _display_send_result(retry_result)
                st.rerun()
            else:
                st.error("Email service failed to send the message.")

    for item in items:
        with st.expander(f"{item.get('sent_at')} — {item.get('candidate_name')} — {item.get('subject')}"):
            st.markdown(f"**Email Type:** {item.get('email_type')}  ")
            st.markdown(f"**Decision:** {item.get('decision')}  ")
            st.markdown(f"**Job:** {item.get('job_title')}  ")
            st.markdown(f"**Status:** {item.get('status')}  ")
            if item.get("error_message"):
                st.caption(item.get("error_message"))
            st.text(item.get('subject') or "")
            st.write(item.get('body') or "")

    cols = st.columns(3)
    if cols[0].button("Previous", disabled=page <= 1):
        st.session_state["comm_history_page"] = page - 1
        st.rerun()
    cols[1].write(f"Page {page}")
    if cols[2].button("Next", disabled=len(items) < 25):
        st.session_state["comm_history_page"] = page + 1
        st.rerun()


def _render_compose():
    st.markdown("### Compose Communication")
    candidate_id = st.session_state.get("comm_draft_candidate_id")
    interview_id = st.session_state.get("comm_draft_interview_id")
    job_id = st.session_state.get("comm_draft_job_id")
    email_type = st.session_state.get("comm_draft_email_type", EMAIL_TYPE_OPTIONS[0])

    candidates = get_candidates_cached()
    candidate_map = {c["id"]: c for c in candidates}
    jobs = get_jobs_cached()
    job_map = {j["id"]: j for j in jobs}

    if not candidate_id:
        candidate_id = st.selectbox("Candidate", [0] + [c["id"] for c in candidates], format_func=lambda x: "Select a candidate" if x == 0 else candidate_map[x]["name"])
    else:
        st.markdown(f"**Candidate:** {candidate_map.get(candidate_id, {}).get('name', 'Unknown')}  ")

    if not job_id:
        job_id = st.selectbox("Job", [0] + [j["id"] for j in jobs], format_func=lambda x: "Select a job" if x == 0 else job_map[x]["title"])
    else:
        st.markdown(f"**Job:** {job_map.get(job_id, {}).get('title', 'Unknown')}  ")

    email_type = st.selectbox("Email Type", EMAIL_TYPE_OPTIONS, index=EMAIL_TYPE_OPTIONS.index(email_type) if email_type in EMAIL_TYPE_OPTIONS else 0)

    if st.button("Generate Draft"):
        if not candidate_id or not job_id:
            st.error("Candidate and Job are required to generate a draft.")
        else:
            # Auto-populate decision from candidate status, sender name, and reply-to email
            candidate = candidate_map.get(candidate_id, {})
            decision = candidate.get("status", "Application Received")
            sender_name = "HR Recruitment Team"
            reply_to = "hr@company.com"  # Default, could be from env
            
            payload = {
                "candidate_id": candidate_id,
                "email_type": email_type,
                "job_id": job_id,
                "interview_id": interview_id,
                "sender_name": sender_name,
                "reply_to_email": reply_to,
            }
            draft = api_client.generate_communication_email(payload)
            if draft:
                st.session_state["comm_draft"] = draft
                st.session_state["comm_sender_name"] = sender_name
                st.session_state["comm_reply_to"] = reply_to
                st.session_state["comm_draft_candidate_id"] = candidate_id
                st.session_state["comm_draft_job_id"] = job_id
                st.session_state["comm_draft_interview_id"] = interview_id
                st.session_state["comm_draft_email_type"] = email_type
                st.session_state["comm_draft_decision"] = decision
                st.rerun()
            else:
                st.error("Failed to generate communication draft.")

    draft = st.session_state.get("comm_draft")
    if draft:
        subject = st.text_input("Subject", value=draft.get("subject", ""))
        body = st.text_area("Body", value=draft.get("body", ""), height=260)
        uploaded_file = None
        if email_type == "Offer Letter":
            st.divider()
            st.markdown("### Offer Letter Attachment")
            uploaded_file = file_uploader_simple(
                label="Drag and drop offer letter here",
                accepted_types=["pdf", "docx"],
                max_size_mb=200,
                key="offer_letter_upload"
            )
            st.divider()
            
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Send Email"):
                if uploaded_file and uploaded_file.size > 20 * 1024 * 1024:
                    st.error("Attachment size exceeds 20MB limit.")
                else:
                    # Use auto-populated values
                    candidate = candidate_map.get(candidate_id, {})
                    decision = candidate.get("status", "Application Received")
                    sender_name = st.session_state.get("comm_sender_name", "HR Recruitment Team")
                    reply_to = st.session_state.get("comm_reply_to", "hr@company.com")
                    
                    payload = {
                        "candidate_id": candidate_id,
                        "subject": subject,
                        "body": body,
                        "email_type": email_type,
                        "decision": decision,
                        "interview_id": interview_id,
                        "sender_name": sender_name,
                        "reply_to_email": reply_to,
                    }
                    
                    if uploaded_file:
                        res = api_client.send_communication_email_with_attachment(payload, uploaded_file)
                    else:
                        res = api_client.send_communication_email(payload)
                    if res and res.get("success"):
                        st.success("Email sent and recorded.")
                        st.session_state["comm_draft"] = None
                        api_client.clear_candidates_cache()
                        api_client.clear_interviews_cache()
                        st.rerun()
                    elif res:
                        st.error(res.get("message") or res.get("error_message") or "Email service failed to send the message.")
        with col2:
            if st.button("Clear Draft"):
                st.session_state["comm_draft"] = None
                st.rerun()


def render_communications():
    # Ensure this page content respects the fixed sidebar and has proper width
    st.markdown("""
    <h1 style='font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;'>
        ✉️ Communications Center
    </h1>
    <p style='font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;'>
        Generate, save, and track candidate email communications from a single workspace.
    </p>
    """, unsafe_allow_html=True)

    # Page-scoped CSS to reinforce main content alignment (helps on some Streamlit versions)
    st.markdown(
        """
        <style>
        .block-container { padding-left: 2.5rem !important; padding-right: 2.5rem !important; }
        [data-testid="stMain"] { margin-left: 256px !important; width: calc(100% - 256px) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "comm_view" not in st.session_state:
        st.session_state["comm_view"] = "queue"
    if "comm_history_page" not in st.session_state:
        st.session_state["comm_history_page"] = 1

    cols = st.columns([1, 1, 1])
    if cols[0].button("Pending Queue"):
        st.session_state["comm_view"] = "queue"
    if cols[1].button("Compose Email"):
        st.session_state["comm_view"] = "compose"
    if cols[2].button("History"):
        st.session_state["comm_view"] = "history"

    st.divider()

    if st.session_state["comm_view"] == "queue":
        _render_pending_queue()
    elif st.session_state["comm_view"] == "compose":
        _render_compose()
    else:
        _render_history()
