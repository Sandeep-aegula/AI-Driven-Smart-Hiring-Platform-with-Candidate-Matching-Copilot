import streamlit as st

def render_resume_analysis():
    """Renders Section 5: AI Resume Analysis Component."""
    # st.markdown("<!-- SECTION 5: AI RESUME ANALYSIS -->")
    st.markdown("""
    <div class="custom-card-wrapper" style="margin-bottom: 0px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;">
        <div class="section-title" style="margin-bottom: 0px;">
            <span><i class="fa-solid fa-robot"></i></span> AI Resume Analysis
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    cand_active = st.session_state.selected_candidate
    
    with st.container(border=True):
        # Candidate Info Banner
        avatar_initials = "".join([part[0] for part in cand_active["name"].split()[:2]])
        rec = cand_active["recommendation"]
        badge_style = "badge-strong" if rec == "Strong Match" else ("badge-moderate" if rec == "Moderate Match" else "badge-low")
        
        st.markdown(f"""
        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap;">
                <div style="width: 70px; height: 70px; border-radius: 50%; background-color: #2563EB; color: white; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 24px; box-shadow: 0 4px 10px rgba(37,99,235,0.2);">
                    {avatar_initials}
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                        <h3 style="font-size: 1.4rem; font-weight: 800; color: #0F172A; margin: 0;">{cand_active["name"]}</h3>
                        <span class="{badge_style}">{rec}</span>
                    </div>
                    <p style="font-size: 0.88rem; color: #475569; font-weight: 600; margin: 4px 0 0 0;">{cand_active["role"]} • {cand_active["experience"]} Years Experience</p>
                </div>
                <div style="text-align: right; min-width: 150px;">
                    <div style="font-size: 0.78rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Overall Score</div>
                    <div style="font-size: 2.2rem; font-weight: 800; color: #2563EB; line-height: 1;">{cand_active["match_score"]}%</div>
                </div>
            </div>
            <div style="display: flex; gap: 20px; margin-top: 16px; font-size: 0.8rem; border-top: 1px solid #E2E8F0; padding-top: 12px; color: #64748B; font-weight: 500;">
                <div><i class="fa-solid fa-envelope"></i> {cand_active["email"]}</div>
                <div><i class="fa-solid fa-phone"></i> {cand_active["phone"]}</div>
                <div><i class="fa-solid fa-graduation-cap"></i> {cand_active["education"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs for details
        tabs = st.tabs(["Summary", "Experience & Projects", "Certifications & Skills"])
        
        with tabs[0]:
            st.markdown("#### Resume Summary")
            st.markdown(f"<p style='color: #334155; font-size: 0.92rem; line-height: 1.6;'>{cand_active['summary']}</p>", unsafe_allow_html=True)
            
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            st.markdown(f"**Relevance Alignment Score ({cand_active['match_score']}%)**")
            st.progress(min(1.0, max(0.0, float(cand_active["match_score"]) / 100)))
            
        with tabs[1]:
            st.markdown("#### Experience History")
            st.markdown(f"""
            <div style="margin-bottom: 15px;">
                <div style="font-weight: 700; color: #0F172A; font-size: 0.95rem;">Lead Systems Developer</div>
                <div style="font-size: 0.8rem; color: #64748B; font-weight: 600; margin-bottom: 6px;">Global HR Software Inc • 2022 - Present</div>
                <ul style="font-size: 0.88rem; color: #334155; line-height: 1.5; margin-left: -15px;">
                    <li>Led development of Python backend APIs supporting 10k+ daily users.</li>
                    <li>Orchestrated microservices using Docker packages and automated deployments.</li>
                </ul>
            </div>
            <div>
                <div style="font-weight: 700; color: #0F172A; font-size: 0.95rem;">Software Architect</div>
                <div style="font-size: 0.8rem; color: #64748B; font-weight: 600; margin-bottom: 6px;">Solutions Cloud Systems • 2018 - 2022</div>
                <ul style="font-size: 0.88rem; color: #334155; line-height: 1.5; margin-left: -15px;">
                    <li>Engineered cloud storage pipelines utilizing AWS EC2 & S3 frameworks.</li>
                    <li>Designed core SQL transaction schemas optimizing read latency by 20%.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### Notable Projects")
            for project in cand_active["projects"]:
                st.markdown(f"- **{project.split(' (')[0]}**: {project.split(' (')[1].replace(')', '') if '(' in project else project}")
                
        with tabs[2]:
            st.markdown("#### Active Skills Categorization")
            skills_found_html = "".join([f'<span class="tag-success">✓ {skill}</span>' for skill in cand_active["skills"]])
            st.markdown(f"**Skills Found**<br>{skills_found_html}", unsafe_allow_html=True)
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            missing_skills_html = "".join([f'<span class="tag-missing">✗ {skill}</span>' for skill in cand_active["missing_skills"]])
            st.markdown(f"**Missing Critical Skills**<br>{missing_skills_html}", unsafe_allow_html=True)
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            st.markdown("#### Certifications")
            for cert in cand_active["certifications"]:
                st.markdown(f'<i class="fa-solid fa-trophy" style="color:#F59E0B; margin-right:5px;"></i> {cert}', unsafe_allow_html=True)
