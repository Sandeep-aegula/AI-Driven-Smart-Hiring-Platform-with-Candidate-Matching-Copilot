import streamlit as st
import numpy as np
import time
from frontend.components.file_uploader import file_uploader_simple

def render_upload_resume():
    """Renders Section 4: Upload Resume Area Component."""
    # st.markdown("<!-- SECTION 4: UPLOAD RESUME -->", unsafe_allow_html=True)
    st.markdown("""
    <div class="custom-card-wrapper" style="margin-bottom: 0px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;">
        <div class="section-title" style="margin-bottom: 0px;">
            <span><i class="fa-solid fa-cloud-arrow-up"></i></span> Upload & Analyze Candidate Resume
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("<p style='font-size: 0.88rem; color: #475569; margin-bottom: 12px;'>Upload an applicant's resume file to run AI matching against the job description.</p>", unsafe_allow_html=True)
        
        # Custom File Uploader Component
        uploaded_file = file_uploader_simple(
            label="Drag and drop resume here",
            accepted_types=["pdf", "docx", "doc"],
            max_size_mb=200,
            key="resume_file_uploader_restruct"
        )
        
        # Display Preview & Actions if File is Uploaded
        if uploaded_file is not None:
            file_ext = uploaded_file.name.split(".")[-1].upper()
            file_size_kb = uploaded_file.size / 1024
            
            st.markdown(f"""
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin: 15px 0;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 26px; color: #2563EB;"><i class="fa-solid fa-file-lines"></i></span>
                        <div>
                            <div style="font-weight: 700; color: #0F172A; font-size: 0.9rem;">{uploaded_file.name}</div>
                            <div style="font-size: 0.75rem; color: #64748B;">{file_size_kb:.1f} KB • {file_ext} Document</div>
                        </div>
                    </div>
                    <span class="badge-strong">Ready</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action Buttons
            u_btn_col1, u_btn_col2 = st.columns(2)
            with u_btn_col1:
                if st.button("Upload Resume", width="stretch", key="upload_resume_btn_restruct"):
                    st.toast("File uploaded successfully to HR portal!", icon="📤")
            with u_btn_col2:
                if st.button("Analyze Resume", type="primary", width="stretch", key="analyze_resume_btn_restruct"):
                    # Simulate Analysis Loading Animation
                    progress_text = "Parsing resume formatting..."
                    loading_bar = st.progress(0, text=progress_text)
                    
                    for percent_complete in range(100):
                        time.sleep(0.015)
                        if percent_complete == 35:
                            progress_text = "Extracting skills & competencies..."
                        elif percent_complete == 70:
                            progress_text = "Running semantic matching model..."
                        loading_bar.progress(percent_complete + 1, text=progress_text)
                    
                    # Compute a name based on file
                    base_name = uploaded_file.name.split(".")[0].replace("_", " ").replace("-", " ")
                    clean_name = " ".join([word.capitalize() for word in base_name.split() if word.lower() not in ["resume", "cv"]])
                    if not clean_name:
                        clean_name = "Alex Rivera"
                    
                    # Check requirements & match skills dynamically
                    job_reqs = st.session_state.job_details["required_skills"]
                    
                    # Generate some overlapping skills based on job requirement
                    num_overlap = max(1, len(job_reqs) - 2)
                    candidate_skills = list(np.random.choice(job_reqs, size=min(len(job_reqs), num_overlap), replace=False))
                    # Add standard tools
                    candidate_skills.extend(["Git", "PostgreSQL", "React", "TypeScript"])
                    candidate_skills = list(set(candidate_skills))
                    
                    missing_skills = [s for s in job_reqs if s not in candidate_skills]
                    
                    # Create simulated candidate dictionary
                    new_candidate = {
                        "id": len(st.session_state.candidates_list) + 1,
                        "name": clean_name,
                        "role": st.session_state.job_details["title"],
                        "email": f"{clean_name.lower().replace(' ', '.')}@example.com",
                        "phone": "+1 (555) 074-9281",
                        "experience": 6,
                        "education": "BS in Computer Science, Stanford University",
                        "skills": candidate_skills,
                        "missing_skills": missing_skills,
                        "projects": [
                            "HR Tech Integrator (Engineered API gateway matching platforms)",
                            "Cloud Migration Pipeline (Led Docker container migrations on AWS)"
                        ],
                        "certifications": ["AWS Certified Cloud Practitioner", "Scrum Product Owner"],
                        "summary": f"{clean_name} is an experienced systems professional with a focus on web systems and database integration. Solid competence with technologies like {', '.join(candidate_skills[:4])}.",
                        "match_score": int(len([s for s in job_reqs if s in candidate_skills]) / len(job_reqs) * 100) if job_reqs else 85,
                        "status": "Applied",
                        "recommendation": "Strong Match" if len([s for s in job_reqs if s in candidate_skills]) / len(job_reqs) >= 0.8 else "Moderate Match",
                        "strengths": [
                            f"Strong hands-on experience in: {', '.join(candidate_skills[:3])}.",
                            "Demonstrated track record of deploying applications and handling APIs.",
                            "Solid foundation in software architecture and technical planning."
                        ],
                        "weaknesses": [
                            f"Missing skills: {', '.join(missing_skills[:2]) if missing_skills else 'None'}.",
                            "Limited formal enterprise infrastructure architecture leadership."
                        ],
                        "interview_suggestions": [
                            "API Design: Ask to whiteboard an endpoint architecture.",
                            "Missing Skill Check: Verify knowledge levels regarding missing elements.",
                            "System Scaling: Test how he structures databases for load scaling."
                        ]
                    }
                    
                    # Add to session state candidates list if unique name
                    if not any(c['name'] == new_candidate['name'] for c in st.session_state.candidates_list):
                        st.session_state.candidates_list.append(new_candidate)
                    
                    # Add to recent activity list
                    st.session_state.activities.insert(0, {
                        "icon": "fa-file-lines",
                        "title": "Resume Analyzed",
                        "description": f"{new_candidate['name']} - Match: {new_candidate['match_score']}%",
                        "time": "Just now"
                    })
                    
                    # Update active selection to new candidate
                    for cand in st.session_state.candidates_list:
                        if cand['name'] == new_candidate['name']:
                            st.session_state.selected_candidate = cand
                            break
                    
                    st.toast(f"Analysis Complete! Selected candidate set to {clean_name}", icon="🎉")
                    st.success(f"Successfully processed resume! Detailed reports populated below.")
                    time.sleep(0.5)
                    st.rerun()
        else:
            # Display instructions guide to fill space and explain AI pipeline
            st.markdown("""
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #E2E8F0;">
                <h4 style="font-size: 0.95rem; color: #0F172A; margin-bottom: 12px; font-weight: 700;">
                    <i class="fa-solid fa-wand-magic-sparkles" style="color: #2563EB; margin-right: 6px;"></i> AI Screening Pipeline
                </h4>
                <ul style="list-style-type: none; padding-left: 0; margin: 0; font-size: 0.85rem; color: #475569; line-height: 1.6;">
                    <li style="margin-bottom: 10px; display: flex; gap: 10px; align-items: flex-start;">
                        <span style="color: #2563EB; font-weight: bold;">1.</span>
                        <div><strong>Resume Parsing:</strong> Automatically extracts candidate contact details, work history, and education.</div>
                    </li>
                    <li style="margin-bottom: 10px; display: flex; gap: 10px; align-items: flex-start;">
                        <span style="color: #2563EB; font-weight: bold;">2.</span>
                        <div><strong>Skills Gap Analysis:</strong> Compares candidate skills against job requirements to flag match status.</div>
                    </li>
                    <li style="margin-bottom: 10px; display: flex; gap: 10px; align-items: flex-start;">
                        <span style="color: #2563EB; font-weight: bold;">3.</span>
                        <div><strong>Semantic Alignment:</strong> Ranks compatibility with a dynamic percentage rating based on roles.</div>
                    </li>
                    <li style="margin-bottom: 0; display: flex; gap: 10px; align-items: flex-start;">
                        <span style="color: #2563EB; font-weight: bold;">4.</span>
                        <div><strong>Actionable Recommendations:</strong> Populates strengths, dev areas, and custom interview questions.</div>
                    </li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

