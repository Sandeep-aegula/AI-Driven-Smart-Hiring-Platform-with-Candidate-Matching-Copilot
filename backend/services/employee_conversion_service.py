import logging
from datetime import datetime

from backend.database.data_store import data_store

logger = logging.getLogger(__name__)

async def create_employee_from_candidate(candidate_id: int) -> dict:
    """
    Creates or updates an Employee record from a Candidate record when they are hired.
    Extracts relevant metadata and skills.
    """
    candidate = await data_store.get_candidate(candidate_id)
    if not candidate:
        raise ValueError(f"Candidate {candidate_id} not found.")

    # Determine default department and designation from applications if available
    department = ""
    designation = candidate.get("current_title", "Employee")
    
    apps = candidate.get("applications", [])
    if apps:
        latest_app = apps[-1]
        job_id = latest_app.get("job_id")
        job = await data_store.get_job(job_id)
        if job:
            department = job.get("department", "")
            designation = job.get("title", designation)

    # Format skills to the new Employee skill format
    cand_skills = candidate.get("skills", [])
    emp_skills = []
    for s in cand_skills:
        skill_name = s.get("name") if isinstance(s, dict) else str(s)
        if skill_name:
            emp_skills.append({
                "name": skill_name,
                "proficiency": 50,  # Default proficiency
                "status": "Acquired"
            })
            
    resume_id = None
    resumes = candidate.get("resumes", [])
    if resumes:
        resume_id = resumes[-1].get("id")

    # Prepare payload
    payload = {
        "name": candidate.get("name", "Unknown"),
        "email": candidate.get("email", ""),
        "phone": candidate.get("phone", ""),
        "department": department,
        "designation": designation,
        "joining_date": datetime.utcnow().date().isoformat(),
        "status": "Active",
        "work_location": candidate.get("location", "Remote"),
        "reporting_manager": "",
        "current_project": "",
        "avatar_url": candidate.get("avatar_url", ""),
        "skills": emp_skills,
        "projects": [],
        "performance_history": [],
        "talent_insights": {},
        "notes": candidate.get("notes", []),
        "candidate_id": candidate_id,
        "resume_id": resume_id,
        "linkedin": candidate.get("linkedin", ""),
        "github": candidate.get("github", ""),
        "portfolio": candidate.get("portfolio", ""),
        "education": candidate.get("education", []),
        "experience": candidate.get("experience", [])
    }

    try:
        existing_emp = await data_store.get_employee_by_candidate_id(candidate_id)
        if existing_emp:
            emp_id = existing_emp["id"]
            # To avoid overwriting existing properties like joining date or history if not wanted,
            # we can merge. But for simplicity and consistency with requirements, we update.
            # We don't overwrite joining_date or status or existing lists if they exist in a meaningful way.
            # However, the requirement is "update the existing employee."
            payload["joining_date"] = existing_emp.get("joining_date", payload["joining_date"])
            payload["projects"] = existing_emp.get("projects", [])
            payload["performance_history"] = existing_emp.get("performance_history", [])
            payload["talent_insights"] = existing_emp.get("talent_insights", {})
            employee = await data_store.update_employee(emp_id, payload)
            logger.info(f"Successfully updated Employee {emp_id} from Candidate {candidate_id}.")
            return employee
        else:
            employee = await data_store.create_employee(payload)
            logger.info(f"Successfully converted Candidate {candidate_id} to Employee {employee.get('id')}.")
            return employee
    except Exception as e:
        logger.error(f"Error creating/updating employee from candidate: {e}")
        raise
