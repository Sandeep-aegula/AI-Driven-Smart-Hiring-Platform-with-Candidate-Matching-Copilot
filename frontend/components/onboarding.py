from __future__ import annotations

import streamlit as st
from frontend.components import api_client
from frontend.services.cache import get_jobs_cached
from frontend.components.file_uploader import file_uploader_simple


def render_onboarding():
    """Render the Onboarding & Document Verification page."""

    # Page header
    st.markdown("""
    <h1 style='font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;'>
        📋 Onboarding & Document Verification
    </h1>
    <p style='font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;'>
        Review and verify documents submitted by selected candidates.
    </p>
    """, unsafe_allow_html=True)

    # Page-scoped CSS
    st.markdown(
        """
        <style>
        .block-container { padding-left: 2.5rem !important; padding-right: 2.5rem !important; }
        [data-testid="stMain"] { margin-left: 256px !important; width: calc(100% - 256px) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Initialize session state
    if "onboarding_view" not in st.session_state:
        st.session_state["onboarding_view"] = "list"
    if "selected_onboarding_id" not in st.session_state:
        st.session_state["selected_onboarding_id"] = None

    # Load data
    onboarding_candidates = api_client.get_onboarding_candidates()

    # Calculate summary metrics
    total_candidates = len(onboarding_candidates)
    docs_pending = sum(
        max((c.get("total_required", 0) or 0) - (c.get("verified_count", 0) or 0), 0)
        for c in onboarding_candidates
    )
    docs_verified = sum(c.get("verified_count", 0) or 0 for c in onboarding_candidates)
    ready_count = sum(1 for c in onboarding_candidates if c.get("ready_for_onboarding"))

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Onboarding Candidates", total_candidates)
    with col2:
        st.metric("Documents Pending Review", docs_pending)
    with col3:
        st.metric("Documents Verified", docs_verified)
    with col4:
        st.metric("Ready for Onboarding", ready_count)

    st.divider()

    # Filter section
    with st.expander("Filters", expanded=True):
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        with filter_col1:
            search_query = st.text_input("Search by name or email", placeholder="Search...")
        with filter_col2:
            jobs = get_jobs_cached()
            job_options = [{"id": 0, "title": "All Jobs"}] + jobs
            selected_job = st.selectbox(
                "Job",
                options=[j["id"] for j in job_options],
                format_func=lambda x: next((j["title"] for j in job_options if j["id"] == x), "All Jobs"),
            )
        with filter_col3:
            status_filter = st.selectbox(
                "Onboarding Status",
                ["All", "Pending", "Documents Uploaded", "Under Review", "Documents Incomplete",
                 "Documents Rejected", "Documents Verified", "Ready for Onboarding", "Onboarding Completed"],
            )
        with filter_col4:
            verif_filter = st.selectbox(
                "Verification Status",
                ["All", "Complete", "Incomplete"],
            )

    # Apply filters
    filtered_candidates = onboarding_candidates
    if search_query:
        search_lower = search_query.lower()
        filtered_candidates = [
            c for c in filtered_candidates
            if search_lower in c.get("candidate_name", "").lower()
            or search_lower in c.get("candidate_email", "").lower()
        ]
    if selected_job != 0:
        filtered_candidates = [c for c in filtered_candidates if c.get("job_id") == selected_job]
    if status_filter != "All":
        filtered_candidates = [c for c in filtered_candidates if c.get("status") == status_filter]
    else:
        # Exclude completed onboarding records from the 'All' view by default
        filtered_candidates = [c for c in filtered_candidates if c.get("status") != "Onboarding Completed"]

    if verif_filter == "Complete":
        filtered_candidates = [c for c in filtered_candidates if c.get("verification_status") == "Complete" or c.get("ready_for_onboarding")]
    elif verif_filter == "Incomplete":
        filtered_candidates = [c for c in filtered_candidates if c.get("verification_status") != "Complete" and not c.get("ready_for_onboarding")]

    # Display candidates
    if not filtered_candidates:
        st.info("No candidates are currently available for onboarding.")
        return

    # Candidate list table
    st.subheader("Onboarding Candidates")

    # Display as table
    for candidate in filtered_candidates:
        with st.container():
            cand_col1, cand_col2, cand_col3, cand_col4, cand_col5, cand_col6, cand_col7, cand_col8 = st.columns([2.1, 2, 1.5, 1.25, 1.1, 1.1, 1.1, 1])

            with cand_col1:
                st.markdown(f"**{candidate.get('candidate_name', 'N/A')}**")
                st.caption(candidate.get('candidate_email', ''))
            with cand_col2:
                st.markdown(f"{candidate.get('job_title', 'N/A')}")
                st.caption(f"{candidate.get('department', '')} | {candidate.get('designation', '')}")
            with cand_col3:
                st.markdown(f"{candidate.get('candidate_phone', 'N/A')}")
                st.caption("Phone")
            with cand_col4:
                selected_date = candidate.get('selected_date') or candidate.get('created_at') or 'N/A'
                st.markdown(f"{selected_date[:10] if isinstance(selected_date, str) and len(selected_date) >= 10 else selected_date}")
                st.caption("Selected Date")
            with cand_col5:
                status = candidate.get('status', 'Pending')
                status_emoji = {
                    'Pending': '⏳',
                    'Documents Uploaded': '📤',
                    'Under Review': '👀',
                    'Documents Incomplete': '⚠️',
                    'Documents Rejected': '❌',
                    'Documents Verified': '✅',
                    'Ready for Onboarding': '🎯',
                    'Onboarding Completed': '🏁',
                }.get(status, '📋')
                st.markdown(f"{status_emoji} {status}")
            with cand_col6:
                verification = candidate.get('verification_status', 'Incomplete')
                st.markdown(f"**{verification}**")
                st.caption("Verification")
            with cand_col7:
                pct = candidate.get('completion_percentage', 0)
                st.progress(pct / 100)
                st.caption(f"{pct}% Complete")
                st.caption(f"Required: {candidate.get('total_required', 0)} | Verified: {candidate.get('verified_count', 0)}")
            with cand_col8:
                if st.button("View Details", key=f"view_{candidate['id']}"):
                    st.session_state["selected_onboarding_id"] = candidate["id"]
                    st.session_state["onboarding_view"] = "details"
                    st.rerun()

            st.divider()

    # Detail view
    if st.session_state["onboarding_view"] == "details" and st.session_state["selected_onboarding_id"]:
        _render_onboarding_details(st.session_state["selected_onboarding_id"])


def _render_onboarding_details(onboarding_id: int):
    """Render the detailed view for a specific onboarding candidate."""

    st.divider()

    # Back button
    if st.button("← Back to List"):
        st.session_state["onboarding_view"] = "list"
        st.session_state["selected_onboarding_id"] = None
        st.rerun()

    # Get details
    details = api_client.get_onboarding_details(onboarding_id)
    if not details:
        st.error("Failed to load onboarding details.")
        return

    # Header
    st.subheader(f"👤 {details['candidate']['name']}")

    # Candidate info
    info_col1, info_col2, info_col3 = st.columns(3)
    with info_col1:
        st.markdown("**Candidate Information**")
        st.write(f"📧 {details['candidate']['email']}")
        st.write(f"📞 {details['candidate']['phone']}")
        st.write(f"📍 {details['candidate']['location'] or 'N/A'}")
    with info_col2:
        st.markdown("**Job Information**")
        st.write(f"💼 {details['job']['title']}")
        st.write(f"🏢 {details['job']['department']}")
    with info_col3:
        st.markdown("**Onboarding Information**")
        st.write(f"📅 Joining: {details['joining_date'] or 'Not set'}")
        st.write(f"🗓️ Selected: {details.get('selected_date') or 'Not set'}")
        st.write(f"🏢 Dept: {details['department']}")
        st.write(f"📋 Role: {details['designation']}")

    st.divider()

    # Progress section
    progress = details.get("progress", {})
    prog_col1, prog_col2, prog_col3, prog_col4, prog_col5, prog_col6 = st.columns(6)
    with prog_col1:
        st.metric("Required Docs", progress.get("total_required", 0))
    with prog_col2:
        st.metric("Uploaded", progress.get("uploaded", 0))
    with prog_col3:
        st.metric("Verified", progress.get("verified", 0))
    with prog_col4:
        st.metric("Pending", progress.get("pending", 0))
    with prog_col5:
        st.metric("Rejected", progress.get("rejected", 0))
    with prog_col6:
        ready = progress.get("ready_for_onboarding", False)
        if ready:
            st.success("🎯 Ready for Onboarding")
        else:
            st.warning(f"⏳ {progress.get('completion_percentage', 0)}% Complete")

    if details.get("status") != "Onboarding Completed":
        complete_disabled = not ready or details.get("status") == "Onboarding Completed"
        if st.button("Complete Onboarding", width="stretch", type="primary", disabled=complete_disabled):
            result = api_client.complete_onboarding(details["id"])
            if result and result.get("status_code") == 200:
                st.success("Onboarding completed and employee created.")
                st.rerun()
            elif result:
                st.error(result.get("message") or "Failed to complete onboarding")
            else:
                st.error("Failed to complete onboarding")

    st.divider()

    # Document requirements
    st.subheader("📄 Document Checklist")

    for req in details.get("document_requirements", []):
        with st.expander(f"{req['document_name']} ({req['current_status']})", expanded=True):
            req_col1, req_col2, req_col3 = st.columns([2, 2, 1])

            with req_col1:
                st.markdown(f"**Type:** {req['document_type']}")
                st.markdown(f"**Required:** {'Yes' if req['required'] else 'No'}")
                st.markdown(f"**Status:** {req['current_status']}")

            with req_col2:
                current_doc = req.get("current_document")
                if current_doc:
                    st.markdown(f"**File:** {current_doc['original_filename']}")
                    st.markdown(f"**Version:** {current_doc['version']}")
                    st.markdown(f"**Size:** {current_doc.get('file_size', 0) / 1024:.1f} KB")
                    if current_doc.get("uploaded_at"):
                        st.markdown(f"**Uploaded:** {current_doc['uploaded_at'][:10]}")

                    # Action buttons
                    action_col1, action_col2, action_col3 = st.columns(3)

                    with action_col1:
                        if req["current_status"] == "Uploaded" or req["current_status"] == "Under Review":
                            if st.button("✅ Verify", key=f"verify_{current_doc['document_id']}"):
                                result = api_client.verify_onboarding_document(current_doc['document_id'])
                                if result:
                                    st.success("Document verified!")
                                    st.rerun()
                                else:
                                    st.error("Failed to verify document")

                    with action_col2:
                        if req["current_status"] != "Verified":
                            reject_reason = st.text_area("Rejection reason", key=f"reject_reason_{current_doc['document_id']}", height=60)
                            if st.button("❌ Reject", key=f"reject_{current_doc['document_id']}"):
                                if reject_reason.strip():
                                    result = api_client.reject_onboarding_document(
                                        current_doc['document_id'],
                                        rejection_reason=reject_reason
                                    )
                                    if result:
                                        st.success("Document rejected!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to reject document")
                                else:
                                    st.error("Please provide a rejection reason")

                    with action_col3:
                        if req["current_status"] != "Verified":
                            reupload_msg = st.text_area("Re-upload message", key=f"reupload_msg_{current_doc['document_id']}", height=60)
                            if st.button("🔄 Request Re-upload", key=f"reupload_{current_doc['document_id']}"):
                                if reupload_msg.strip():
                                    result = api_client.request_document_reupload(
                                        current_doc['document_id'],
                                        reupload_message=reupload_msg
                                    )
                                    if result:
                                        st.success("Re-upload requested!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to request re-upload")
                                else:
                                    st.error("Please provide a message")
                else:
                    st.warning("No document uploaded yet")

            # Document upload section
            with req_col3:
                if req["current_status"] in ["Missing", "Rejected", "Re-upload Requested", None]:
                    uploaded_file = file_uploader_simple(
                        label="Drag and drop document here",
                        accepted_types=["pdf", "png", "jpg", "jpeg", "docx"],
                        max_size_mb=200,
                        key=f"upload_{req['requirement_id']}"
                    )
                    if uploaded_file:
                        if st.button("Upload", key=f"btn_upload_{req['requirement_id']}"):
                            file_bytes = uploaded_file.getvalue()
                            result = api_client.upload_onboarding_document(
                                requirement_id=req['requirement_id'],
                                file_bytes=file_bytes,
                                filename=uploaded_file.name,
                                mime_type=uploaded_file.type or "application/octet-stream"
                            )
                            if result:
                                st.success("Document uploaded!")
                                st.rerun()
                            else:
                                st.error("Failed to upload document")

            # Version history
            if req.get("version_history") and len(req["version_history"]) > 1:
                with st.expander("📜 Version History"):
                    for version in req["version_history"]:
                        st.markdown(f"""
                        - **Version {version['version']}**: {version['original_filename']}
                          - Status: {version['status']}
                          - Uploaded: {version.get('uploaded_at', 'N/A')}
                          - Verified by: {version.get('verified_by', 'N/A') if version['status'] == 'Verified' else 'N/A'}
                          - Rejected by: {version.get('rejected_by', 'N/A') if version['status'] == 'Rejected' else 'N/A'}
                        """)


def refresh_onboarding():
    """Clear caches and refresh onboarding data."""
    api_client.clear_onboarding_cache()