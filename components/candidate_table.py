import streamlit as st

def render_candidate_table():
    """Renders Section 7: Searchable Candidate Database Table."""
    st.markdown("<!-- SECTION 7: CANDIDATE TABLE -->", unsafe_allow_html=True)
    st.markdown("""
    <div class="custom-card-wrapper" style="margin-bottom: 24px;">
        <div class="section-title" style="margin-bottom: 0px; border-bottom: none; padding-bottom: 0px;">
            <span><i class="fa-solid fa-user-group"></i></span> Candidate Database & Screening Board
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Filter candidate database based on search input
    query = st.session_state.search_query.strip().lower()
    filtered_candidates = []
    
    for candidate in st.session_state.candidates_list:
        name_match = query in candidate["name"].lower()
        role_match = query in candidate["role"].lower()
        skill_match = any(query in s.lower() for s in candidate["skills"])
        if name_match or role_match or skill_match or not query:
            filtered_candidates.append(candidate)

    # Render Table Header
    t_col0, t_col1, t_col2, t_col3, t_col4, t_col5, t_col6 = st.columns([1, 2.5, 2.5, 3.5, 1.2, 1.8, 2.5])
    with t_col0:
        st.markdown("**Photo**")
    with t_col1:
        st.markdown("**Candidate Name**")
    with t_col2:
        st.markdown("**Position & Exp**")
    with t_col3:
        st.markdown("**Core Skills**")
    with t_col4:
        st.markdown("**Match**")
    with t_col5:
        st.markdown("**Current Status**")
    with t_col6:
        st.markdown("**Actions**")

    st.markdown("<div style='border-bottom: 2px solid #E2E8F0; margin-bottom: 12px; margin-top: 4px;'></div>", unsafe_allow_html=True)

    # Render Table Rows
    if not filtered_candidates:
        st.markdown("<p style='text-align: center; color: #64748B; font-weight: 500; padding: 20px 0;'>No candidates match your search query.</p>", unsafe_allow_html=True)
    else:
        for idx, candidate in enumerate(filtered_candidates):
            row_container = st.container()
            with row_container:
                # Columns
                r_col0, r_col1, r_col2, r_col3, r_col4, r_col5, r_col6 = st.columns([1, 2.5, 2.5, 3.5, 1.2, 1.8, 2.5])
                
                # 1. Avatar Photo
                with r_col0:
                    initials = "".join([n[0] for n in candidate["name"].split()[:2]])
                    border_style = "box-shadow: 0 0 0 3px #3B82F6;" if candidate["id"] == st.session_state.selected_candidate["id"] else ""
                    st.markdown(f"""
                    <div style="display: flex; justify-content: center; align-items: center; height: 50px;">
                        <div style="width: 44px; height: 44px; border-radius: 50%; background-color: #EFF6FF; color: #2563EB; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 14px; border: 2px solid #DBEAFE; {border_style}">
                            {initials}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                # 2. Candidate Name
                with r_col1:
                    st.markdown(f"""
                    <div style="padding-top: 6px;">
                        <div style="font-weight: 700; color: #0F172A; font-size: 0.92rem;">{candidate["name"]}</div>
                        <div style="font-size: 0.75rem; color: #64748B;">{candidate["email"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                # 3. Position & Exp
                with r_col2:
                    st.markdown(f"""
                    <div style="padding-top: 6px;">
                        <div style="font-weight: 600; color: #334155; font-size: 0.88rem;">{candidate["role"]}</div>
                        <div style="font-size: 0.75rem; color: #64748B;">{candidate["experience"]} Yrs Experience</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                # 4. Core Skills
                with r_col3:
                    tags_html = "".join([f'<span class="tag">{s}</span>' for s in candidate["skills"][:3]])
                    if len(candidate["skills"]) > 3:
                        tags_html += f'<span class="tag" style="background-color: #E2E8F0; color: #475569; border-color: #CBD5E1;">+{len(candidate["skills"]) - 3} more</span>'
                    st.markdown(f'<div style="padding-top: 10px;">{tags_html}</div>', unsafe_allow_html=True)
                    
                # 5. Match %
                with r_col4:
                    score = candidate["match_score"]
                    score_color = "#10B981" if score >= 85 else ("#F59E0B" if score >= 70 else "#EF4444")
                    st.markdown(f"""
                    <div style="padding-top: 12px; font-weight: 800; font-size: 1.05rem; color: {score_color};">
                        {score}%
                    </div>
                    """, unsafe_allow_html=True)
                    
                # 6. Status Badge
                with r_col5:
                    status = candidate["status"]
                    status_class = "badge-strong" if status == "Shortlisted" else ("badge-blue" if status == "Applied" else ("badge-moderate" if status == "Interview Scheduled" else "badge-low"))
                    st.markdown(f'<div style="padding-top: 12px;"><span class="{status_class}">{status}</span></div>', unsafe_allow_html=True)
                    
                # 7. Actions (View details, Shortlist, Reject)
                with r_col6:
                    act_cols = st.columns(3)
                    with act_cols[0]:
                        if st.button("View", key=f"comp_tbl_view_{candidate['id']}", help=f"Analyze {candidate['name']}'s profile"):
                            st.session_state.selected_candidate = candidate
                            st.toast(f"Displaying profile details for {candidate['name']}!", icon="🔍")
                            st.rerun()
                    with act_cols[1]:
                        is_shortlisted = candidate["status"] == "Shortlisted"
                        if st.button("Shortlist", key=f"comp_tbl_short_{candidate['id']}", help=f"Shortlist {candidate['name']}", disabled=is_shortlisted):
                            candidate["status"] = "Shortlisted"
                            st.session_state.activities.insert(0, {
                                "icon": "fa-circle-check",
                                "title": "Candidate Shortlisted",
                                "description": f"{candidate['name']} status updated to Shortlisted",
                                "time": "Just now"
                            })
                            st.toast(f"{candidate['name']} added to Shortlisted group!", icon="✅")
                            st.rerun()
                    with act_cols[2]:
                        is_rejected = candidate["status"] == "Rejected"
                        if st.button("Reject", key=f"comp_tbl_rej_{candidate['id']}", help=f"Reject {candidate['name']}", disabled=is_rejected):
                            candidate["status"] = "Rejected"
                            st.session_state.activities.insert(0, {
                                "icon": "fa-circle-xmark",
                                "title": "Candidate Rejected",
                                "description": f"{candidate['name']} status updated to Rejected",
                                "time": "Just now"
                            })
                            st.toast(f"{candidate['name']} marked as Rejected.", icon="❌")
                            st.rerun()
                            
                st.markdown("<div style='border-bottom: 1px solid #F1F5F9; margin-top: 8px; margin-bottom: 8px;'></div>", unsafe_allow_html=True)
                
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
