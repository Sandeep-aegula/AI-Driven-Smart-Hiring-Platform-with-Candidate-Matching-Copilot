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


def _render_pending_queue():
    st.markdown("### Pending Communications")
    st.write("Use this queue to follow up on important candidate decisions.")
    pending = api_client.get_pending_communications()
    if not pending:
        st.info("No pending communications at this time.")
        return

    for item in pending:
        with st.expander(f"{item.get('candidate_name')} — {item.get('decision')} ({item.get('days_pending')}d pending)"):
            st.markdown(f"**Job:** {item.get('job_title')}  ")
            st.markdown(f"**Round:** {item.get('round') or 'N/A'}  ")
            st.markdown(f"**Email Type:** {item.get('implied_email_type')}  ")
            st.markdown(f"**Draft Saved:** {'Yes' if item.get('draft_saved') else 'No'}  ")
            if st.button("Draft Email", key=f"draft_pending_{item.get('candidate_id')}_{item.get('interview_id')}"):
                st.session_state["comm_draft_candidate_id"] = item.get('candidate_id')
                st.session_state["comm_draft_job_id"] = item.get('job_id')
                st.session_state["comm_draft_interview_id"] = item.get('interview_id')
                st.session_state["comm_draft_email_type"] = item.get('implied_email_type')
                st.session_state["comm_draft_decision"] = item.get('decision')
                st.session_state["comm_view"] = "compose"
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
