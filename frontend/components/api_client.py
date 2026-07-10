import httpx
import logging

logger = logging.getLogger(__name__)
API_URL = "http://localhost:8000"

def get_jobs(search="", department="All", status="All", sort_by="updated_at"):
    try:
        resp = httpx.get(f"{API_URL}/jobs", params={"search": search, "department": department, "status": status, "sort_by": sort_by})
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        return []

def get_job(job_id):
    try:
        resp = httpx.get(f"{API_URL}/jobs/{job_id}")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error fetching job: {e}")
        return None

def create_job(payload):
    try:
        resp = httpx.post(f"{API_URL}/jobs", json=payload)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        return None

def update_job(job_id, payload):
    try:
        resp = httpx.put(f"{API_URL}/jobs/{job_id}", json=payload)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error updating job: {e}")
        return None

def delete_job(job_id):
    try:
        resp = httpx.delete(f"{API_URL}/jobs/{job_id}")
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        return False

def archive_job(job_id):
    try:
        resp = httpx.post(f"{API_URL}/jobs/{job_id}/archive")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error archiving job: {e}")
        return None

def clone_job(job_id):
    try:
        resp = httpx.post(f"{API_URL}/jobs/{job_id}/clone")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error cloning job: {e}")
        return None

def generate_jd(payload):
    try:
        resp = httpx.post(f"{API_URL}/jobs/generate-jd", json=payload, timeout=90.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error generating JD: {e}")
        return None

def get_candidates(search="", status="All", skill="All"):
    try:
        resp = httpx.get(f"{API_URL}/candidates", params={"search": search, "status": status, "skill": skill})
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error fetching candidates: {e}")
        return []

def get_candidate(candidate_id):
    try:
        resp = httpx.get(f"{API_URL}/candidates/{candidate_id}")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error fetching candidate: {e}")
        return None

def add_candidate_note(candidate_id, note):
    try:
        resp = httpx.post(f"{API_URL}/candidates/{candidate_id}/notes", params={"note": note})
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error adding candidate note: {e}")
        return None

def update_candidate_status(candidate_id, status):
    try:
        resp = httpx.post(f"{API_URL}/candidates/{candidate_id}/status", params={"status": status})
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error updating candidate status: {e}")
        return None

def upload_resume(file_bytes, filename):
    try:
        files = {"file": (filename, file_bytes, "application/octet-stream")}
        resp = httpx.post(f"{API_URL}/resume/upload", files=files, timeout=90.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        return None

def get_upload_history():
    try:
        resp = httpx.get(f"{API_URL}/resume/history")
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error getting upload history: {e}")
        return []

def screen_candidate_against_job(candidate_id, job_id):
    try:
        resp = httpx.get(f"{API_URL}/ai-screening", params={"candidate_id": candidate_id, "job_id": job_id}, timeout=90.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error screening candidate: {e}")
        return None

def approve_candidate(candidate_id):
    try:
        resp = httpx.post(f"{API_URL}/ai-screening/approve", params={"candidate_id": candidate_id})
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error approving candidate: {e}")
        return None

def shortlist_candidate(candidate_id):
    try:
        resp = httpx.post(f"{API_URL}/ai-screening/shortlist", params={"candidate_id": candidate_id})
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error shortlisting candidate: {e}")
        return None

def reject_candidate(candidate_id):
    try:
        resp = httpx.post(f"{API_URL}/ai-screening/reject", params={"candidate_id": candidate_id})
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error rejecting candidate: {e}")
        return None

def get_interviews():
    try:
        resp = httpx.get(f"{API_URL}/interviews")
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error fetching interviews: {e}")
        return []

def schedule_interview(payload):
    try:
        resp = httpx.post(f"{API_URL}/interviews", json=payload)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error scheduling interview: {e}")
        return None

def update_interview_status(interview_id, status):
    try:
        resp = httpx.put(f"{API_URL}/interviews/{interview_id}/status", params={"status": status})
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error updating interview status: {e}")
        return None

def add_interview_feedback(interview_id, feedback_notes, recommendation):
    try:
        payload = {"feedback_notes": feedback_notes, "recommendation": recommendation}
        resp = httpx.post(f"{API_URL}/interviews/{interview_id}/feedback", json=payload)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error adding interview feedback: {e}")
        return None

def generate_interview_questions(stage, skills):
    try:
        payload = {"stage": stage, "skills": skills}
        resp = httpx.post(f"{API_URL}/interviews/generate-questions", json=payload)
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        return []

def get_employees():
    try:
        resp = httpx.get(f"{API_URL}/employees")
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error fetching employees: {e}")
        return []

def get_employee(employee_id):
    try:
        resp = httpx.get(f"{API_URL}/employees/{employee_id}")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error fetching employee: {e}")
        return None
