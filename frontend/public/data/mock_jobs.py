"""Mock job data for the public-facing HirePilot website.

This module provides temporary frontend-only job data so the public
Careers page can be built and tested without backend integration.
Later this should be replaced with an API call.
"""

MOCK_JOBS = [
    {
        "id": 1,
        "title": "AI/ML Engineer",
        "department": "Engineering",
        "location": "Hyderabad",
        "employment_type": "Full-Time",
        "required_skills": ["Python", "Machine Learning", "Deep Learning"],
        "short_description": "Build AI-powered products and intelligent recruitment solutions.",
        "description": (
            "We are looking for an AI/ML Engineer to help us build intelligent systems "
            "that power the next generation of recruitment technology. You will work on "
            "candidate matching, resume parsing, and predictive hiring models."
        ),
        "responsibilities": [
            "Design and implement machine learning models for candidate-job matching.",
            "Collaborate with backend engineers to integrate AI capabilities into the platform.",
            "Monitor model performance and retrain pipelines as needed.",
            "Stay up to date with the latest AI research and apply it to real-world hiring problems.",
        ],
        "preferred_qualifications": [
            "Experience with NLP and resume parsing.",
            "Familiarity with ATS and recruitment workflows.",
            "Published research or open-source contributions.",
        ],
        "experience_requirements": "3+ years of experience in machine learning or AI engineering.",
    },
    {
        "id": 2,
        "title": "Python Backend Developer",
        "department": "Technology",
        "location": "Bengaluru",
        "employment_type": "Full-Time",
        "required_skills": ["Python", "FastAPI", "MySQL"],
        "short_description": "Develop scalable backend services and APIs.",
        "description": (
            "Join our backend team to build and maintain the APIs and services that power "
            "HirePilot. You will work with modern Python frameworks, design clean architectures, "
            "and ensure the platform remains fast and reliable."
        ),
        "responsibilities": [
            "Design and develop RESTful APIs using FastAPI.",
            "Write clean, maintainable, and well-tested Python code.",
            "Optimize database queries and application performance.",
            "Collaborate with frontend and AI teams on integration requirements.",
        ],
        "preferred_qualifications": [
            "Experience with async Python and SQLAlchemy.",
            "Knowledge of message queues and background task processing.",
            "Experience with cloud deployment and containerization.",
        ],
        "experience_requirements": "2+ years of backend development with Python.",
    },
    {
        "id": 3,
        "title": "Data Analyst",
        "department": "Analytics",
        "location": "Hyderabad",
        "employment_type": "Full-Time",
        "required_skills": ["SQL", "Python", "Tableau"],
        "short_description": "Analyze business data and generate actionable insights.",
        "description": (
            "We are seeking a Data Analyst to turn complex hiring data into clear, actionable "
            "insights. You will support product, engineering, and leadership teams with "
            "dashboards, reports, and data-driven recommendations."
        ),
        "responsibilities": [
            "Build and maintain dashboards for recruitment metrics.",
            "Analyze hiring pipelines, time-to-hire, and candidate quality.",
            "Present insights to non-technical stakeholders.",
            "Improve data quality and reliability across reporting systems.",
        ],
        "preferred_qualifications": [
            "Experience with BI tools such as Tableau or Power BI.",
            "Knowledge of statistical analysis and A/B testing.",
            "Familiarity with HR metrics and recruitment analytics.",
        ],
        "experience_requirements": "1-3 years of experience in data analysis or business intelligence.",
    },
    {
        "id": 4,
        "title": "Frontend Developer",
        "department": "Technology",
        "location": "Remote",
        "employment_type": "Full-Time",
        "required_skills": ["HTML", "CSS", "JavaScript"],
        "short_description": "Build responsive and user-friendly web interfaces.",
        "description": (
            "We are looking for a Frontend Developer to create intuitive, responsive, and "
            "visually polished user interfaces for both the public careers website and the "
            "internal HR portal."
        ),
        "responsibilities": [
            "Develop responsive web interfaces using modern HTML, CSS, and JavaScript.",
            "Work closely with designers to implement high-fidelity UI components.",
            "Ensure cross-browser compatibility and accessibility.",
            "Optimize frontend performance and loading times.",
        ],
        "preferred_qualifications": [
            "Experience with component-based UI frameworks.",
            "Knowledge of design systems and accessibility standards.",
            "Familiarity with Streamlit or similar Python web frameworks.",
        ],
        "experience_requirements": "1-3 years of frontend development experience.",
    },
]


def get_all_jobs():
    """Return all mock jobs."""
    return list(MOCK_JOBS)


def get_job_by_id(job_id):
    """Return a single mock job by ID, or None if not found."""
    for job in MOCK_JOBS:
        if job["id"] == job_id:
            return job
    return None


def search_jobs(query="", department="All", location="All", employment_type="All"):
    """Filter mock jobs based on search and filters."""
    results = list(MOCK_JOBS)

    if query:
        q = query.lower()
        results = [
            job
            for job in results
            if q in job["title"].lower()
            or q in job["short_description"].lower()
            or any(q in skill.lower() for skill in job["required_skills"])
        ]

    if department != "All":
        results = [job for job in results if job["department"] == department]

    if location != "All":
        results = [job for job in results if job["location"] == location]

    if employment_type != "All":
        results = [
            job for job in results if job["employment_type"] == employment_type
        ]

    return results
