import logging

import pandas as pd
import streamlit as st
from frontend.components import api_client
from frontend.services.cache import get_jobs_cached
from frontend.utils.constants import SHORTLISTABLE_CANDIDATE_STATUSES


logger = logging.getLogger(__name__)


def render_candidates():
    st.markdown(
        """
        <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
          👥 Candidate Management
        </h1>
        <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
          Review, compare, and email candidates using AI.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Init state
    if "selected_candidate_id" not in st.session_state:
        st.session_state.selected_candidate_id = None
    if "compare_mode" not in st.session_state:
        st.session_state.compare_mode = False

    # Route logic
    if st.session_state.compare_mode:
        _render_compare_view()
    elif st.session_state.selected_candidate_id:
        _render_candidate_profile(st.session_state.selected_candidate_id)
    else:
        _render_candidates_list()


def _render_candidates_list():
    jobs = get_jobs_cached()
    job_opts = {j["id"]: j["title"] for j in jobs}
    job_opts[0] = "All Jobs"

    # Filters
    cf1, cf2, cf3 = st.columns([2, 1.5, 2])
    with cf1:
        job_filter = st.selectbox(
            "Job Filter",
            options=list(job_opts.keys()),
            format_func=lambda x: job_opts[x],
            index=list(job_opts.keys()).index(0),
        )
    with cf2:
        status_filter = st.selectbox(
            "Status",
            ["All", "Applied", "Under Review", "Shortlisted", "Interview Scheduled", "Interviewed", "Hired", "Rejected"],
        )
    with cf3:
        min_score = st.slider("Minimum Match Score", 0, 100, 0)

    job_id_param = None if job_filter == 0 else job_filter
    try:
        candidates = api_client.get_candidates(
            status=status_filter,
            job_id=job_id_param,
            min_match_score=min_score,
            raise_on_error=True,
        )
    except Exception as exc:
        st.error(f"Failed to load candidates: {exc}")
        return

    logger.info("Candidates tab received %s candidate rows", len(candidates))

    if not candidates:
        st.info("No candidates found.")
        return

    valid_candidates = [candidate for candidate in candidates if isinstance(candidate, dict)]
    if len(valid_candidates) != len(candidates):
        logger.warning("Candidates tab received %s invalid row(s)", len(candidates) - len(valid_candidates))
        st.warning("Some candidate records were ignored because the API returned invalid data.")

    candidates = valid_candidates

    if not candidates:
        st.info("No candidates found.")
        return

    df_data = []
    for c in candidates:
        df_data.append(
            {
                "App ID": c.get("application_id", ""),
                "ID": c.get("id", ""),
                "Email": c.get("email", ""),
                "Job": c.get("job_title", ""),
                "Match": f"{c.get('match_score', 0)}%",
                "Name": c.get("name", "Unknown"),
                "Status": c.get("status", "Unknown"),
                "Experience": f"{c.get('years_experience', 0)} Yrs",
                "Rec": c.get("hire_recommendation", "N/A"),
                "Updated": c.get("updated_at", "")[:10] if c.get("updated_at") else "",
            }
        )
    df = pd.DataFrame(df_data)
    # Ensure App ID is the first column for shortlist; keep ID as secondary reference
    df = df[["App ID", "ID", "Email", "Job", "Match", "Name", "Status", "Experience", "Rec", "Updated"]]

    event = st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
        column_config={
            "App ID": st.column_config.NumberColumn(width="small"),
            "ID": st.column_config.NumberColumn(width="small"),
            "Email": st.column_config.TextColumn(width="medium"),
            "Job": st.column_config.TextColumn(width="medium"),
            "Match": st.column_config.TextColumn(width="small"),
            "Status": st.column_config.TextColumn(width="small"),
        },
    )
    selected_rows = event.selection.rows if hasattr(event, "selection") else []

    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    with c1:
        if st.button(
            "View Profile",
            type="primary",
            disabled=len(selected_rows) != 1,
            width="stretch",
        ):
            st.session_state.selected_candidate_id = int(df.iloc[selected_rows[0]]["ID"])
            st.rerun()
    with c2:
        if st.button(
            "Compare Selected",
            disabled=len(selected_rows) < 2 or len(selected_rows) > 4,
            width="stretch",
        ):
            if job_filter == 0:
                st.error("Please select a specific Job Filter first to compare candidates.")
            else:
                st.session_state.compare_cands = [int(df.iloc[r]["ID"]) for r in selected_rows]
                st.session_state.compare_job_id = job_filter
                st.session_state.compare_mode = True
                st.rerun()
    with c3:
        shortlist_disabled = len(selected_rows) == 0
        # Check if any selected candidates are in non-shortlistable status
        non_shortlistable_selected = False
        if selected_rows:
            for r in selected_rows:
                candidate_status = df.iloc[r]["Status"]
                if candidate_status not in SHORTLISTABLE_CANDIDATE_STATUSES:
                    non_shortlistable_selected = True
                    break
        if non_shortlistable_selected:
            shortlist_disabled = True
        shortlist_label = (
            f"Shortlist Selected ({len(selected_rows)})" if selected_rows else "Shortlist Selected"
        )
        if st.button(
            shortlist_label,
            disabled=shortlist_disabled,
            width="stretch",
            help="Cannot shortlist candidates that are already Hired, Rejected, Shortlisted, or Interviewed" if non_shortlistable_selected else None,
        ):
            selected_app_ids = [int(df.iloc[r]["App ID"]) for r in selected_rows]
            with st.spinner(f"Shortlisting {len(selected_app_ids)} candidate(s)..."):
                result = api_client.shortlist_bulk(selected_app_ids)
                if result and result.get("success"):
                    updated = result.get("updated_count", 0)
                    failed = result.get("failed_count", 0)
                    if failed == 0:
                        st.success(f"✅ Shortlisted {updated} candidate(s) successfully.")
                    else:
                        st.warning(
                            f"⚠️ Shortlisted {updated} candidate(s); {failed} failed.")
                        for failure in result.get("failures", []):
                            app_id = failure.get("application_id", "?")
                            error = failure.get("error", "Unknown error")
                            st.error(f"Application {app_id}: {error}")
                    st.rerun()
                else:
                    st.error("Failed to shortlist selected candidates.")
    with c4:
        if st.button("Clear Selection", width="stretch"):
            st.session_state.compare_cands = []
            st.rerun()

    if len(selected_rows) > 4:
        st.warning("Please select a maximum of 4 candidates to compare.")


def _render_compare_view():
    st.button("← Back to List", on_click=lambda: st.session_state.update({"compare_mode": False}))
    st.markdown("### Candidate Comparison")

    with st.spinner("AI is analyzing and comparing candidates..."):
        res = api_client.compare_candidates(
            st.session_state.compare_cands,
            st.session_state.compare_job_id,
        )
    if not res:
        st.error("Comparison failed.")
        return

    table = res.get("comparison_table", [])
    cols = st.columns(len(table))
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**{table[i].get('name')}**")
            st.markdown("**Strengths:**\n" + table[i].get("strengths", ""))
            st.markdown("**Weaknesses:**\n" + table[i].get("weaknesses", ""))
            st.info(f"**AI Recommendation:**\n{res.get('recommendation', '')}")


def _render_candidate_profile(candidate_id: int):
    st.button("← Back to List", on_click=lambda: st.session_state.update({"selected_candidate_id": None}))
    candidate = api_client.get_candidate(candidate_id)
    if not candidate:
        st.error("Candidate not found.")
        return

    resume_summary = candidate.get("resume_summary") or candidate.get("summary", "No resume summary available.")
    skills = [s.get("name") if isinstance(s, dict) else str(s) for s in candidate.get("skills", [])]
    experience_items = (
        candidate.get("experience")
        if isinstance(candidate.get("experience"), list)
        else ([candidate.get("experience")] if candidate.get("experience") else [])
    )
    education_items = (
        candidate.get("education")
        if isinstance(candidate.get("education"), list)
        else ([candidate.get("education")] if candidate.get("education") else [])
    )
    projects = (
        candidate.get("projects")
        if isinstance(candidate.get("projects"), list)
        else ([candidate.get("projects")] if candidate.get("projects") else [])
    )
    certifications = (
        candidate.get("certifications")
        if isinstance(candidate.get("certifications"), list)
        else ([candidate.get("certifications")] if candidate.get("certifications") else [])
    )
    skill_breakdown = candidate.get("skill_match_breakdown", {}) or {}

    hire_rec = candidate.get("hire_recommendation") or (
        "Strong Hire"
        if candidate.get("match_score", 0) >= 85
        else "Hire"
        if candidate.get("match_score", 0) >= 70
        else "Hold"
        if candidate.get("match_score", 0) >= 50
        else "Reject"
    )
    status = candidate.get("status", "N/A")
    match_score = candidate.get("match_score", 0)
    current_title = candidate.get("current_title", "")
    location = candidate.get("location", "")

    st.markdown(f"## {candidate['name']}")
    st.markdown(f"**{current_title}** • {location}")

    cards = st.columns([1.25, 1, 1, 1])
    cards[0].metric("Match Score", f"{match_score}%", delta=hire_rec)
    cards[1].metric("Status", status)
    cards[2].metric("Recommendation", hire_rec)
    cards[3].metric("Experience", f"{candidate.get('years_experience', 0)} yrs")

    t1, t2, t3, t4, t5 = st.tabs(
        ["Candidate Overview", "AI Ranking", "Skill Gap", "Recruiter Actions", "Email"]
    )

    with t1:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### Candidate Information")
            st.write(f"**Email:** {candidate.get('email', 'N/A')}")
            st.write(f"**Phone:** {candidate.get('phone', 'N/A')}")
            st.write(f"**LinkedIn:** {candidate.get('linkedin', 'N/A')}")
            st.write(f"**GitHub:** {candidate.get('github', 'N/A')}")
            st.write(f"**Portfolio:** {candidate.get('portfolio', 'N/A')}")
            st.write(f"**Current Title:** {current_title}")
            st.write(f"**Location:** {location}")
            st.write(f"**Status:** {status}")
            st.write(f"**Tags:** {', '.join(candidate.get('tags', [])) or 'N/A'}")
            st.markdown("#### Resume Overview")
            st.write(resume_summary)

        with c2:
            st.markdown("#### Resume Matching")
            st.write(f"**Overall Match Score:** {match_score}%")
            st.write(f"**AI Recommendation:** {hire_rec}")
            st.markdown("**Skill Match Breakdown**")
            if skill_breakdown:
                for key, value in skill_breakdown.items():
                    st.write(f"- **{key.replace('_', ' ').title()}:** {value}")
            else:
                st.write("No breakdown available.")

            st.markdown("#### Skills")
            st.write(", ".join(skills) if skills else "No skills available.")

            st.markdown("#### Experience")
            if experience_items:
                for item in experience_items:
                    st.write(f"- {item}")
            else:
                st.write("No experience details available.")

            st.markdown("#### Education")
            if education_items:
                for item in education_items:
                    st.write(f"- {item}")
            else:
                st.write("No education details available.")

            st.markdown("#### Projects")
            if projects:
                for item in projects:
                    st.write(f"- {item}")
            else:
                st.write("No project details available.")

            st.markdown("#### Certifications")
            if certifications:
                for item in certifications:
                    st.write(f"- {item}")
            else:
                st.write("No certifications available.")

    with t2:
        st.markdown("#### Candidate Ranking & AI Suitability")
        rank_res = {}
        if "ranking_explanation" in candidate:
            rank_res = {"ranking_explanation": candidate["ranking_explanation"]}
        else:
            with st.spinner("AI is evaluating candidate rank..."):
                rank_res = api_client.get_candidate_rank(candidate_id)
        if rank_res:
            api_client.clear_candidates_cache()
            st.write(
                rank_res.get("ranking_explanation", "AI ranking is unavailable at this time.")
            )

        st.markdown("#### Recommendation Summary")
        st.write(f"**Final AI Decision:** {hire_rec}")
        st.write(f"**Hiring Confidence:** {match_score}%")
        st.write(f"**Candidate Strengths:** {candidate.get('summary', 'Not available.')}")
        st.write(f"**Candidate Concerns:** {candidate.get('concerns', 'No concerns recorded.')}")

    with t3:
        st.markdown("#### Skill Gap Analysis")
        gap_res = {}
        if "skill_gap_analysis" in candidate:
            gap_res = candidate["skill_gap_analysis"]
        else:
            with st.spinner("AI is analyzing skill gaps..."):
                gap_res = api_client.get_candidate_skill_gap(candidate_id)
        if gap_res and "error" not in gap_res:
            api_client.clear_candidates_cache()
            _render_skill_gap_ui(gap_res)

            st.markdown("#### Skill Match Details")
            st.write(
                f"**Required Skills:** {', '.join(gap_res.get('required_skills', [])) or 'N/A'}"
            )
            st.write(
                f"**Existing Skills:** {', '.join(gap_res.get('matched_skills', [])) or 'N/A'}"
            )
            st.write(
                f"**Missing Skills:** {', '.join(gap_res.get('missing_skills', [])) or 'N/A'}"
            )
            st.write(
                f"**Skill Match Percentage:** {gap_res.get('match_percentage', 0)}%"
            )
            st.write(
                f"**Learning Recommendations:** {gap_res.get('improvement_suggestions', 'No recommendations available.')}"
            )
        else:
            st.error("Failed to generate skill gap analysis.")

    with t4:
        st.markdown("#### Recruiter Actions")
        action_cols = st.columns(4)
        with action_cols[0]:
            if st.button("🌟 Shortlist", width="stretch"):
                api_client.update_candidate_status(candidate_id, "Shortlisted")
                st.success("Candidate shortlisted.")
                st.rerun()
        with action_cols[1]:
            if st.button("📅 Move to Interview", width="stretch"):
                api_client.update_candidate_status(candidate_id, "Interview Scheduled")
                st.session_state["current_page"] = "Interviews"
                st.session_state["interview_view"] = "Schedule"
                st.session_state["schedule_candidate_id"] = candidate_id
                st.rerun()
        with action_cols[2]:
            if st.button("❌ Reject", width="stretch"):
                api_client.update_candidate_status(candidate_id, "Rejected")
                st.error("Candidate rejected.")
                st.rerun()
        with action_cols[3]:
            if st.button("🎉 Hire", width="stretch"):
                api_client.update_candidate_status(candidate_id, "Hired")
                st.toast("Candidate moved to hiring onboarding.", icon="🎉")
                st.rerun()

        st.markdown("---")

        selected_decision = st.selectbox(
            "Final AI Decision",
            ["Strong Hire", "Hire", "Hold", "Reject"],
            index=["Strong Hire", "Hire", "Hold", "Reject"].index(hire_rec)
            if hire_rec in ["Strong Hire", "Hire", "Hold", "Reject"]
            else 2,
        )
        confidence = st.slider("Hiring Confidence", 0, 100, match_score)
        recruiter_note = st.text_area(
            "Recruiter Notes",
            value="",
            placeholder="Add notes for the hiring team...",
        )
        if st.button("Save Decision & Note"):
            api_client.add_candidate_note(
                candidate_id,
                f"Decision: {selected_decision}. Notes: {recruiter_note}",
            )
            st.success("Decision and note saved.")
            st.rerun()

        if candidate.get("notes"):
            st.markdown("#### Past Recruiter Notes")
            for note in candidate.get("notes", []):
                st.info(
                    f"**{note.get('author')}**: {note.get('note')} ({note.get('created_at', '')[:10]})"
                )

    with t5:
        st.markdown("#### AI Email Generator")
        apps = candidate.get("applications", [])
        if not apps:
            st.warning("Candidate must be tied to a job to generate context-aware emails.")
        else:
            job_id = apps[0].get("job_id")
            c1, c2 = st.columns([1, 2])
            with c1:
                email_type = st.selectbox(
                    "Email Type",
                    [
                        "Interview Invitation",
                        "Selection",
                        "Rejection",
                        "Additional Information Request",
                        "Offer Letter",
                    ],
                )
                if st.button("Generate Draft", type="primary", width="stretch"):
                    with st.spinner("AI drafting email..."):
                        res = api_client.generate_candidate_email(
                            candidate_id, email_type, job_id
                        )
                    if res:
                        st.session_state[f"email_subj_{candidate_id}"] = res.get(
                            "subject", ""
                        )
                        st.session_state[f"email_body_{candidate_id}"] = res.get(
                            "body", ""
                        )
                    else:
                        st.error("Failed to generate draft.")

            with c2:
                subj_key = f"email_subj_{candidate_id}"
                body_key = f"email_body_{candidate_id}"
                if subj_key in st.session_state:
                    subj = st.text_input("Subject", value=st.session_state[subj_key])
                    body = st.text_area(
                        "Body",
                        value=st.session_state[body_key],
                        height=220,
                    )
                    if st.button("Send Email", type="primary"):
                        res = api_client.send_candidate_email(candidate_id, subj, body)
                        if res and res.get("success"):
                            st.success("Email sent and saved to history.")
                            st.session_state.pop(subj_key, None)
                            st.session_state.pop(body_key, None)
                            api_client.clear_candidates_cache()
                            st.rerun()
                        elif res:
                            st.error(res.get("message") or res.get("error_message") or "Email service failed to send the message.")

            st.markdown("---")
            st.markdown("#### Email History")
            history = api_client.get_candidate_email_history(candidate_id)
            if not history:
                st.write("No emails sent yet.")
            for msg in history:
                with st.expander(
                    f"{msg.get('sent_at', '')[:10]} - {msg.get('subject', 'No Subject')} ({msg.get('status', '')})"
                ):
                    st.write(msg.get("body", ""))


def _render_skill_gap_ui(gap: dict):
    st.write(f"**Match Percentage:** {gap.get('match_percentage')}%")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("✅ **Matched Skills**")
        for s in gap.get("matched_skills", []):
            st.write(f"- {s}")
    with col2:
        st.markdown("❌ **Missing Skills**")
        for s in gap.get("missing_skills", []):
            st.write(f"- {s}")
    st.markdown("**Improvement Suggestions**")
    st.info(gap.get("improvement_suggestions", "None"))
