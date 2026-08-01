from __future__ import annotations

import streamlit as st
from frontend.components import api_client
from frontend.services.cache import get_candidates_cached, get_jobs_cached

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
    st.markdown("### Pending Queue")
    st.write("Candidates shortlisted and waiting for communication.")
    st.caption("Select candidates to send emails in bulk.")

    pending = fetch_pending_communications()

    if not pending:
        st.info("No pending shortlisted candidates. Shortlist candidates from the Candidate Management page.")
        return

    st.markdown(f"**{len(pending)} candidates awaiting communication**")

    # Initialize selection
    if "comm_selected_ids" not in st.session_state:
        st.session_state.comm_selected_ids = []

    # Bulk action section
    col_b1, col_b2, col_b3 = st.columns([3, 1, 1])

    with col_b1:
        select_all = st.checkbox("Select All", key="select_all_pending")

    with col_b2:
        if st.button("Select All Selected", width="stretch"):
            st.session_state.comm_selected_ids = [p.get("id") for p in pending]
            st.rerun()

    with col_b3:
        if st.button("Clear Selection", width="stretch"):
            st.session_state.comm_selected_ids = []
            st.rerun()

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # Display pending candidates
    for item in pending:
        comm_id = item.get("id")
        is_selected = comm_id in st.session_state.comm_selected_ids

        with st.container():
            col_cb, col_info = st.columns([1, 8])

            with col_cb:
                if st.checkbox("", value=is_selected, key=f"comm_chk_{comm_id}"):
                    if comm_id not in st.session_state.comm_selected_ids:
                        st.session_state.comm_selected_ids.append(comm_id)
                else:
                    if comm_id in st.session_state.comm_selected_ids:
                        st.session_state.comm_selected_ids.remove(comm_id)

            with col_info:
                with st.expander(f"{item.get('candidate_name')} — {item.get('job_title')}"):
                    st.markdown(f"**Email:** {item.get('candidate_email')}")
                    st.markdown(f"**Job:** {item.get('job_title')}")
                    st.markdown(f"**Department:** {item.get('department', 'N/A')}")
                    st.markdown(f"**Round:** {item.get('round') or 'Initial Screening'}")
                    st.markdown(f"**Status:** {item.get('status')}")
                    days = item.get("days_pending", 0)
                    st.caption(f"Queued: {days} days ago")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Bulk send section
    if len(st.session_state.comm_selected_ids) > 0:
        st.markdown(f"""
        <div style="background:#EEF2FF; border:1px solid #C7D2FE; border-radius:8px; padding:12px 16px; margin-bottom:16px;">
            <span style="font-weight:600; color:#4F46E5;">{len(st.session_state.comm_selected_ids)} candidates selected</span>
        </div>
        """, unsafe_allow_html=True)

        with st.form(key="bulk_email_form"):
            st.markdown("#### Send Bulk Email")

            col_e1, col_e2 = st.columns(2)
            with col_e1:
                bulk_subject = st.text_input("Email Subject", value="Interview Invitation - Next Steps")
            with col_e2:
                sender_name = st.text_input("Sender Name", value="HR Recruitment Team")

            bulk_body = st.text_area(
                "Email Body",
                value="Dear {{candidate_name}},\n\nWe are pleased to inform you that your application for the position of {{job_title}} has been shortlisted for further consideration.\n\nPlease find the details for the next round of interviews below.\n\nBest regards,\nHR Team",
                height=200
            )

            st.caption("Use {{candidate_name}} and {{job_title}} as placeholders for personalization.")

            col_send, col_clear = st.columns([1, 1])
            with col_send:
                submit_bulk = st.form_submit_button(f"Send to {len(st.session_state.comm_selected_ids)} Candidates", type="primary", width="stretch")

            with col_clear:
                clear_btn = st.form_submit_button("Clear", width="stretch")

            if submit_bulk:
                with st.spinner(f"Sending emails to {len(st.session_state.comm_selected_ids)} candidates..."):
                    result = send_bulk_communications(
                        st.session_state.comm_selected_ids,
                        bulk_subject,
                        bulk_body,
                        sender_name
                    )
                    if result and result.get("success"):
                        st.success(f"✅ {result.get('message')}")
                        st.session_state.comm_selected_ids = []
                        st.rerun()

            if clear_btn:
                st.session_state.comm_selected_ids = []
                st.rerun()


def _render_history():
    st.markdown("### Sent & Draft History")
    query = st.text_input("Filter by candidate name, subject or email type")
    status = st.selectbox("Status", ["All", "Sent", "Draft"], index=0)
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

    for item in items:
        with st.expander(f"{item.get('sent_at')} — {item.get('candidate_name')} — {item.get('subject')}"):
            st.markdown(f"**Email Type:** {item.get('email_type')}  ")
            st.markdown(f"**Decision:** {item.get('decision')}  ")
            st.markdown(f"**Job:** {item.get('job_title')}  ")
            st.markdown(f"**Status:** {item.get('status')}  ")
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
            uploaded_file = st.file_uploader("Upload Offer Letter", type=["pdf", "docx"], label_visibility="collapsed")
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
                        
                    if res:
                        st.success("Email sent and recorded.")
                        st.session_state["comm_draft"] = None
                        api_client.clear_candidates_cache()
                        api_client.clear_interviews_cache()
                        st.rerun()
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
