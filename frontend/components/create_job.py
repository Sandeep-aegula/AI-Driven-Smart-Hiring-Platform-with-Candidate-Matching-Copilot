import streamlit as st

def render_create_job():
    """Renders Section 3: Create Job Requirement Form Component."""
    st.markdown("<!-- SECTION 3: CREATE JOB REQUIREMENT -->", unsafe_allow_html=True)
    st.markdown("""
    <div class="custom-card-wrapper" style="margin-bottom: 0px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;">
        <div class="section-title" style="margin-bottom: 0px;">
            <span><i class="fa-solid fa-clipboard-list"></i></span> Create Job Requirement
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Form wrapper
    with st.container(border=True):
        j_col1, j_col2 = st.columns(2)
        
        with j_col1:
            job_title = st.text_input("Job Title", value=st.session_state.job_details["title"], help="Enter the formal title of the recruitment position")
            
            department = st.selectbox(
                "Department",
                options=["Engineering", "Data & AI", "Product Management", "Design", "Human Resources", "Sales & Marketing"],
                index=["Engineering", "Data & AI", "Product Management", "Design", "Human Resources", "Sales & Marketing"].index(st.session_state.job_details["department"]),
                help="Select the internal department coordinating this hire"
            )
            
            location = st.selectbox(
                "Location",
                options=["Remote", "Hybrid (SF Office)", "Hybrid (NY Office)", "San Francisco, CA", "New York, NY", "London, UK"],
                index=["Remote", "Hybrid (SF Office)", "Hybrid (NY Office)", "San Francisco, CA", "New York, NY", "London, UK"].index(st.session_state.job_details["location"]),
                help="Select the geographic or workplace arrangement"
            )
            
            emp_type = st.selectbox(
                "Employment Type",
                options=["Full-time", "Part-time", "Contract", "Internship"],
                index=["Full-time", "Part-time", "Contract", "Internship"].index(st.session_state.job_details["employment_type"]),
                help="Choose employment classification"
            )
            
            education_req = st.selectbox(
                "Education Required",
                options=["Bachelor's Degree", "Master's Degree", "PhD", "No Degree Required"],
                index=["Bachelor's Degree", "Master's Degree", "PhD", "No Degree Required"].index(st.session_state.job_details["education"] + " Degree" if "Degree" not in st.session_state.job_details["education"] else st.session_state.job_details["education"]),
                help="Target education level of potential candidates"
            )

        with j_col2:
            # Min & Max Experience Sliders
            exp_range = st.slider(
                "Experience Required (Years)",
                min_value=0,
                max_value=20,
                value=(st.session_state.job_details["min_exp"], st.session_state.job_details["max_exp"]),
                help="Select the range of professional work experience required"
            )
            
            # Salary Range Inputs
            sal_range = st.slider(
                "Salary Range ($ USD)",
                min_value=50000,
                max_value=300000,
                value=(st.session_state.job_details["min_salary"], st.session_state.job_details["max_salary"]),
                step=5000,
                format="$%d",
                help="Select candidate base salary parameters"
            )
            
            # Technologies list (At least 20 dummy technologies)
            tech_options = [
                "Python", "SQL", "Docker", "Git", "Machine Learning", "AWS", "FastAPI",
                "PyTorch", "TensorFlow", "Kubernetes", "CI/CD", "React", "TypeScript",
                "Node.js", "Java", "C++", "Go", "NoSQL", "Redis", "GCP", "Azure",
                "Apache Spark", "Hadoop", "Tableau", "Pandas", "NumPy", "GraphQL",
                "PostgreSQL", "Terraform", "Linux", "Elasticsearch", "Figma", "Sass"
            ]
            
            req_skills = st.multiselect(
                "Required Skills",
                options=tech_options,
                default=st.session_state.job_details["required_skills"],
                help="Must-have competencies for applicant ranking (Select at least 5)"
            )
            
            pref_skills = st.multiselect(
                "Preferred Skills",
                options=tech_options,
                default=st.session_state.job_details["preferred_skills"],
                help="Nice-to-have capabilities giving candidates an edge"
            )

        # Full-width JD / Responsibilities
        job_desc = st.text_area("Job Description Summary", value=st.session_state.job_details["description"], height=95, help="Brief overview outlining role context and main scope")
        job_resp = st.text_area("Key Responsibilities", value=st.session_state.job_details["responsibilities"], height=95, help="Primary duties of the role, one item per line")
        
        # Form buttons
        form_btn_col1, form_btn_col2, form_btn_col3 = st.columns([1, 1, 3])
        with form_btn_col1:
            if st.button("Save Job", type="primary", width="stretch", key="save_job_btn_restruct"):
                st.session_state.job_details = {
                    "title": job_title,
                    "department": department,
                    "location": location,
                    "employment_type": emp_type,
                    "min_exp": exp_range[0],
                    "max_exp": exp_range[1],
                    "min_salary": sal_range[0],
                    "max_salary": sal_range[1],
                    "education": education_req.replace(" Degree", ""),
                    "required_skills": req_skills,
                    "preferred_skills": pref_skills,
                    "description": job_desc,
                    "responsibilities": job_resp
                }
                st.toast("Job requirement updated successfully!", icon="📋")
                st.success("Hiring criteria saved! Analysis updates reflecting automatically.")
                st.rerun()
        with form_btn_col2:
            if st.button("Reset Form", width="stretch", key="reset_job_btn_restruct"):
                if 'job_details' in st.session_state:
                    del st.session_state.job_details
                st.toast("Job form reset to defaults", icon="🔄")
                st.rerun()
