import streamlit as st

def initialize_session_state():
    """Initializes the database states inside Streamlit session_state for reactive updates."""
    # Seed Candidates List
    if 'candidates_list' not in st.session_state:
        st.session_state.candidates_list = [
            {
                "id": 1,
                "name": "Sarah Jenkins",
                "role": "Senior Full-Stack Engineer",
                "email": "sarah.jenkins@example.com",
                "phone": "+1 (555) 019-2834",
                "experience": 8,
                "education": "MS in Computer Science, Georgia Tech",
                "skills": ["Python", "SQL", "Docker", "Git", "Machine Learning", "AWS", "FastAPI", "React", "TypeScript", "CI/CD"],
                "missing_skills": ["Kubernetes", "PyTorch"],
                "projects": [
                    "Automated Resume Screener (NLP based parsing & matching)",
                    "Cloud-native E-commerce Platform (Microservices architecture on AWS)"
                ],
                "certifications": ["AWS Certified Solutions Architect", "Professional Scrum Master (PSM I)"],
                "summary": "Sarah is a highly experienced software engineer with a strong background in building scalable web applications and cloud deployments. She is proficient in both frontend and backend development with strong knowledge of ML and DevOps practices.",
                "match_score": 91,
                "status": "Shortlisted",
                "recommendation": "Strong Match",
                "strengths": [
                    "Expert knowledge of Python, SQL, and modern web frameworks like FastAPI & React.",
                    "Deep experience deploying and scaling applications on AWS using Docker & CI/CD.",
                    "Strong foundational understanding of Machine Learning workflows and deployment."
                ],
                "weaknesses": [
                    "Lacks extensive experience with container orchestration platforms like Kubernetes.",
                    "Has basic exposure to deep learning frameworks (PyTorch/TensorFlow) but no heavy training experience."
                ],
                "interview_suggestions": [
                    "System Design: Ask her to design a scalable real-time notifications system on AWS.",
                    "Practical Backend: Deep dive into FastAPI concurrency and SQLAlchemy optimization.",
                    "Frontend: Ask how she handles state management in large React projects."
                ]
            },
            {
                "id": 2,
                "name": "David Chen",
                "role": "Data Scientist / AI Engineer",
                "email": "david.chen@example.com",
                "phone": "+1 (555) 024-8192",
                "experience": 4,
                "education": "BS in Data Science, UC Berkeley",
                "skills": ["Python", "SQL", "Machine Learning", "PyTorch", "TensorFlow", "Docker", "Git", "Pandas", "NumPy"],
                "missing_skills": ["AWS", "FastAPI", "Kubernetes"],
                "projects": [
                    "E-commerce Recommendation Engine (Collaborative filtering & deep retrieval)",
                    "Computer Vision Defect Detector (YOLOv8 custom object detection model)"
                ],
                "certifications": ["Google Cloud Professional Data Engineer", "TensorFlow Developer Certificate"],
                "summary": "David has a solid foundation in machine learning and data engineering, with practical experience building and deploying predictive models. He is passionate about computer vision and generative AI.",
                "match_score": 85,
                "status": "Interview Scheduled",
                "recommendation": "Strong Match",
                "strengths": [
                    "Strong ML fundamentals and mathematical understanding of model architectures.",
                    "Hands-on experience with deep learning frameworks (PyTorch, TensorFlow) and computer vision.",
                    "Highly clean, modular coding practices for data science projects."
                ],
                "weaknesses": [
                    "Limited experience in API development and backend web frameworks (FastAPI/Flask).",
                    "Cloud infrastructure experience is primarily GCP-focused; AWS knowledge is minimal."
                ],
                "interview_suggestions": [
                    "ML Theory: Discuss how he optimizes hyperparameters and prevents overfitting in deep models.",
                    "Coding: Live coding task on building a data preprocessing pipeline in Pandas.",
                    "Production: Ask how he would deploy a PyTorch model into a containerized application."
                ]
            },
            {
                "id": 3,
                "name": "Emily Taylor",
                "role": "Backend Developer",
                "email": "emily.taylor@example.com",
                "phone": "+1 (555) 013-5749",
                "experience": 5,
                "education": "BS in Software Engineering, UT Austin",
                "skills": ["Python", "SQL", "FastAPI", "Docker", "Git", "Redis", "PostgreSQL", "MongoDB", "CI/CD"],
                "missing_skills": ["Machine Learning", "AWS"],
                "projects": [
                    "Microservice API Gateway (High-throughput routing and authentication layer)",
                    "Real-time Chat Backend (Websocket-based messaging infrastructure on Redis)"
                ],
                "certifications": ["Certified Kubernetes Administrator (CKA)", "Oracle Certified Professional: Java Developer"],
                "summary": "Emily is a backend specialist with experience developing high-performance REST APIs and managing database architectures. She is proficient in container orchestration and backend performance tuning.",
                "match_score": 78,
                "status": "Applied",
                "recommendation": "Moderate Match",
                "strengths": [
                    "Superb understanding of database systems (PostgreSQL, NoSQL) and caching strategies (Redis).",
                    "Expert in building web services using FastAPI/Python and Java.",
                    "Solid understanding of infrastructure orchestration using Kubernetes and Docker."
                ],
                "weaknesses": [
                    "Zero exposure to Machine Learning algorithms and data science workflows.",
                    "AWS cloud deployment knowledge is secondary; primarily works with on-premises servers."
                ],
                "interview_suggestions": [
                    "Concurrency: Ask her to compare multi-threading, multi-processing, and async programming in Python.",
                    "Database Design: Designing a relational schema for a complex application with active caching.",
                    "Kubernetes: Discuss her experience troubleshooting container crashes using kubectl."
                ]
            },
            {
                "id": 4,
                "name": "Marcus Thompson",
                "role": "DevOps Engineer",
                "email": "marcus.t@example.com",
                "phone": "+1 (555) 092-3847",
                "experience": 6,
                "education": "BS in Information Technology, Purdue",
                "skills": ["Docker", "Git", "AWS", "Kubernetes", "Terraform", "Linux", "CI/CD", "GCP", "Python"],
                "missing_skills": ["Machine Learning", "SQL", "FastAPI"],
                "projects": [
                    "Multi-region AWS Migration (Migrated 200+ microservices using Terraform)",
                    "Zero-downtime CI/CD Pipeline (Automated builds, security tests, and deployments)"
                ],
                "certifications": ["AWS Certified DevOps Engineer - Professional", "Terraform Associate"],
                "summary": "Marcus is a cloud infrastructure specialist focused on automation, infrastructure as code, and continuous deployment. He is passionate about building secure and resilient cloud networks.",
                "match_score": 62,
                "status": "Applied",
                "recommendation": "Low Match",
                "strengths": [
                    "Expert in Terraform, Kubernetes, Docker, and CI/CD tools (GitHub Actions, GitLab CI).",
                    "Deep understanding of cloud networking, security, and IAM compliance on AWS and GCP.",
                    "Strong system administration and scripting skills in Bash/Linux."
                ],
                "weaknesses": [
                    "Coding skills in Python are focused primarily on script automation; not a software developer.",
                    "No database design or SQL profiling skills, and zero familiarity with AI/ML tools."
                ],
                "interview_suggestions": [
                    "IaC: Ask him to describe best practices for managing complex multi-environment state files in Terraform.",
                    "SRE Principles: Discuss how he manages monitoring and alerting configurations (Prometheus/Grafana).",
                    "Python Scripting: Test simple automation/scripting tasks to check python logic."
                ]
            },
            {
                "id": 5,
                "name": "Jessica Patel",
                "role": "Frontend Developer",
                "email": "jessica.patel@example.com",
                "phone": "+1 (555) 048-2947",
                "experience": 3,
                "education": "BS in Web Design, NYU",
                "skills": ["React", "TypeScript", "HTML/CSS", "Git", "Figma", "JavaScript", "Redux", "Tailwind CSS"],
                "missing_skills": ["Python", "SQL", "Docker", "Machine Learning", "AWS", "FastAPI"],
                "projects": [
                    "Enterprise Design System (Developed a cohesive UI component library for 5 SaaS apps)",
                    "Interactive Data Analytics Interface (Visualized real-time market data using React-Flow)"
                ],
                "certifications": ["Certified Scrum Developer", "UX/UI Design Certification - Nielsen Norman Group"],
                "summary": "Jessica is a user experience-focused frontend developer with experience creating interactive web interfaces and custom component libraries. She bridges the gap between design and front-end engineering.",
                "match_score": 45,
                "status": "Rejected",
                "recommendation": "Low Match",
                "strengths": [
                    "Strong eye for typography, layouts, and interactive animations (UI/UX).",
                    "Proficient in React, TypeScript, and modern state management tools.",
                    "Expert in translation of Figma files into clean, semantic React code."
                ],
                "weaknesses": [
                    "Lacks knowledge in server-side technologies, APIs, SQL databases, or container tools.",
                    "No exposure to scripting or AI/ML pipelines."
                ],
                "interview_suggestions": [
                    "UI Engineering: Deep dive into responsive layout strategies and styling approaches.",
                    "Figma Collaboration: Ask her to demonstrate her workflows with design systems."
                ]
            }
        ]

    # Seed Default Selected Candidate
    if 'selected_candidate' not in st.session_state:
        st.session_state.selected_candidate = st.session_state.candidates_list[0]

    # Seed Default Job details
    if 'job_details' not in st.session_state:
        st.session_state.job_details = {
            "title": "Senior Python & ML Engineer",
            "department": "Engineering",
            "location": "Remote",
            "employment_type": "Full-time",
            "min_exp": 5,
            "max_exp": 10,
            "min_salary": 120000,
            "max_salary": 180000,
            "education": "Master's",
            "required_skills": ["Python", "SQL", "Docker", "Git", "Machine Learning", "AWS", "FastAPI"],
            "preferred_skills": ["PyTorch", "Kubernetes", "CI/CD", "Redis"],
            "description": "We are looking for a Senior Python & Machine Learning Engineer to join our core AI product team. You will lead the development of our backend microservices, design scalable machine learning workflows, and ensure robust CI/CD integration.",
            "responsibilities": "- Design, build, and deploy production-grade ML models and predictive systems.\n- Develop high-performance backend microservices using FastAPI and SQLAlchemy.\n- Establish CI/CD pipelines and containerize services with Docker and Kubernetes.\n- Collaborate with product managers and frontend teams to deliver premium SaaS features."
        }

    # Seed Timeline Activities
    if 'activities' not in st.session_state:
        st.session_state.activities = [
            {"icon": "fa-file-lines", "title": "Resume Uploaded", "description": "Sarah Jenkins - Senior Full-Stack Engineer", "time": "10 minutes ago"},
            {"icon": "fa-circle-check", "title": "Candidate Shortlisted", "description": "David Chen - Data Scientist", "time": "2 hours ago"},
            {"icon": "fa-calendar-days", "title": "Interview Scheduled", "description": "Emily Taylor - Backend Developer", "time": "Yesterday"},
            {"icon": "fa-briefcase", "title": "Offer Released", "description": "Marcus Thompson - DevOps Engineer", "time": "2 days ago"}
        ]

    # Seed Search Query
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
