import httpx
import logging
import asyncio
import streamlit as st

logger = logging.getLogger(__name__)
API_URL = "http://localhost:8000"


# --- CACHED READ-ONLY API CALLS ---

@st.cache_data(ttl=30, show_spinner=False)
def get_jobs(search="", department="All", status="All", sort_by="updated_at"):
    try:
        resp = httpx.get(f"{API_URL}/jobs", params={"search": search, "department": department, "status": status, "sort_by": sort_by})
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        return []

@st.cache_data(ttl=30, show_spinner=False)
def get_job(job_id):
    try:
        resp = httpx.get(f"{API_URL}/jobs/{job_id}")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error fetching job: {e}")
        return None

@st.cache_data(ttl=30, show_spinner=False)
def get_candidates(search="", status="All", skill="All", job_id=None, min_match_score=0, limit=100, offset=0):
    try:
        params = {"search": search, "status": status, "skill": skill, "min_match_score": min_match_score, "limit": limit, "offset": offset}
        if job_id: params["job_id"] = job_id
        resp = httpx.get(f"{API_URL}/candidates", params=params)
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error fetching candidates: {e}")
        return []

@st.cache_data(ttl=30, show_spinner=False)
def get_candidate(candidate_id):
    try:
        resp = httpx.get(f"{API_URL}/candidates/{candidate_id}")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error fetching candidate: {e}")
        return None

@st.cache_data(ttl=30, show_spinner=False)
def add_candidate_note(candidate_id, note):
    try:
        resp = httpx.post(f"{API_URL}/candidates/{candidate_id}/notes", params={"note": note})
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error adding candidate note: {e}")
        return None

# --- Candidate AI & Email Endpoints ---

@st.cache_data(ttl=300, show_spinner=False)
def get_candidate_rank(candidate_id):
    try:
        resp = httpx.get(f"{API_URL}/candidates/{candidate_id}/rank", timeout=60.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error getting candidate rank: {e}")
        return None

@st.cache_data(ttl=300, show_spinner=False)
def get_candidate_skill_gap(candidate_id):
    try:
        resp = httpx.get(f"{API_URL}/candidates/{candidate_id}/skill-gap", timeout=60.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error getting skill gap: {e}")
        return None

def compare_candidates(candidate_ids, job_id):
    try:
        payload = {"candidate_ids": candidate_ids, "job_id": job_id}
        resp = httpx.post(f"{API_URL}/candidates/compare", json=payload, timeout=90.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error comparing candidates: {e}")
        return None

def generate_candidate_email(candidate_id, email_type, job_id):
    try:
        payload = {"email_type": email_type, "job_id": job_id}
        resp = httpx.post(f"{API_URL}/candidates/{candidate_id}/generate-email", json=payload, timeout=60.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error generating email: {e}")
        return None

def send_candidate_email(candidate_id, subject, body):
    try:
        payload = {"subject": subject, "body": body}
        resp = httpx.post(f"{API_URL}/candidates/{candidate_id}/send-email", json=payload)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return None

def get_candidate_email_history(candidate_id):
    try:
        resp = httpx.get(f"{API_URL}/candidates/{candidate_id}/email-history")
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error getting email history: {e}")
        return []


def get_pending_communications():
    try:
        resp = httpx.get(f"{API_URL}/communications/pending")
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error fetching pending communications: {e}")
        return []


def get_communications_history(page=1, page_size=25, email_type=None, status=None, start_date=None, end_date=None, candidate_name=None, recruiter_name=None):
    try:
        params = {"page": page, "page_size": page_size}
        if email_type: params["email_type"] = email_type
        if status: params["status"] = status
        if start_date: params["start_date"] = start_date
        if end_date: params["end_date"] = end_date
        if candidate_name: params["candidate_name"] = candidate_name
        if recruiter_name: params["recruiter_name"] = recruiter_name
        resp = httpx.get(f"{API_URL}/communications/history", params=params, timeout=10.0)
        return resp.json() if resp.status_code == 200 else {"items": [], "page": page, "page_size": page_size, "total": 0}
    except Exception as e:
        logger.error(f"Error fetching communications history: {e}")
        return {"items": [], "page": page, "page_size": page_size, "total": 0}


def generate_communication_email(payload):
    try:
        resp = httpx.post(f"{API_URL}/communications/generate", json=payload, timeout=60.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error generating communication email: {e}")
        return None


def send_communication_email(payload):
    try:
        resp = httpx.post(f"{API_URL}/communications/send", json=payload, timeout=10.0)
        if resp.status_code == 200:
            clear_candidates_cache()
            clear_interviews_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error sending communication email: {e}")
        return None


def send_communication_email_with_attachment(payload, uploaded_file):
    try:
        data = {k: str(v) if v is not None else "" for k, v in payload.items()}
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        resp = httpx.post(f"{API_URL}/communications/send-multipart", data=data, files=files, timeout=30.0)
        if resp.status_code == 200:
            clear_candidates_cache()
            clear_interviews_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error sending communication email with attachment: {e}")
        return None


def save_communication_draft(payload):
    try:
        resp = httpx.post(f"{API_URL}/communications/save-draft", json=payload, timeout=10.0)
        if resp.status_code == 200:
            clear_candidates_cache()
            clear_interviews_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error saving communication draft: {e}")
        return None

# --- Resumes (New Resume Management) ---

def upload_single_resume(file_bytes, filename, job_id=None):
    try:
        files = {"file": (filename, file_bytes, "application/octet-stream")}
        data = {"job_id": job_id} if job_id else {}
        resp = httpx.post(f"{API_URL}/resumes/upload", files=files, data=data, timeout=90.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error uploading single resume: {e}")
        return None

def start_bulk_upload(files_list, job_id=None):
    """files_list: list of tuples (filename, file_bytes)"""
    try:
        files = [("files", (fname, fbytes, "application/octet-stream")) for fname, fbytes in files_list]
        data = {"job_id": job_id} if job_id else {}
        resp = httpx.post(f"{API_URL}/resumes/bulk-upload", files=files, data=data, timeout=10.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error starting bulk upload: {e}")
        return None

def poll_batch_status(batch_id):
    try:
        resp = httpx.get(f"{API_URL}/resumes/bulk-upload/{batch_id}/status")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error polling batch status: {e}")
        return None

def preview_candidate_draft(candidate_id):
    try:
        resp = httpx.get(f"{API_URL}/resumes/{candidate_id}/preview")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error previewing candidate draft: {e}")
        return None

def update_candidate(candidate_id, payload):
    try:
        resp = httpx.put(f"{API_URL}/resumes/{candidate_id}", json=payload)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error updating candidate: {e}")
        return None

@st.cache_data(ttl=30, show_spinner=False)
def get_upload_history():
    try:
        resp = httpx.get(f"{API_URL}/resumes/history")
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error getting upload history: {e}")
        return []

@st.cache_data(ttl=30, show_spinner=False)
def get_interviews():
    try:
        resp = httpx.get(f"{API_URL}/interviews")
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error fetching interviews: {e}")
        return []

@st.cache_data(ttl=30, show_spinner=False)
def get_employees():
    try:
        resp = httpx.get(f"{API_URL}/employees")
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error fetching employees: {e}")
        return []

@st.cache_data(ttl=30, show_spinner=False)
def get_employee(employee_id):
    try:
        resp = httpx.get(f"{API_URL}/employees/{employee_id}")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error fetching employee: {e}")
        return None


# --- CONCURRENT BATCH FETCHING ---

async def _fetch_dashboard_data_async():
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(f"{API_URL}/jobs", timeout=5.0),
            client.get(f"{API_URL}/candidates", timeout=5.0),
            client.get(f"{API_URL}/interviews", timeout=5.0),
            client.get(f"{API_URL}/employees", timeout=5.0),
            client.get(f"{API_URL}/resume/history", timeout=5.0),
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        parsed = []
        for r in responses:
            if isinstance(r, httpx.Response) and r.status_code == 200:
                parsed.append(r.json())
            else:
                parsed.append([])
        return parsed

@st.cache_data(ttl=30, show_spinner=False)
def get_dashboard_data_batched():
    """Fetch 5 dashboard datasets concurrently using httpx.AsyncClient."""
    try:
        # Use asyncio.run() which properly manages the event loop
        # This avoids the "Event loop is closed" error
        import asyncio
        data = asyncio.run(_fetch_dashboard_data_async())
        return data
    except Exception as e:
        logger.error(f"Failed to batch fetch dashboard data concurrently: {e}")
        # Fallback to sequential cached calls
        return [get_jobs(), get_candidates(), get_interviews(), get_employees(), get_upload_history()]


# --- WRITE OPERATIONS (CLEAR READ CACHES) ---

def clear_jobs_cache():
    get_jobs.clear()
    get_job.clear()
    get_dashboard_data_batched.clear()

def clear_candidates_cache():
    get_candidates.clear()
    get_candidate.clear()
    get_dashboard_data_batched.clear()

def clear_interviews_cache():
    # The app historically exposed both cached and filter-aware interview
    # readers. During Streamlit hot reload a stale plain function can briefly
    # remain bound here; it has no cache to invalidate.
    clear_interviews = getattr(get_interviews, "clear", None)
    if callable(clear_interviews):
        clear_interviews()

    clear_dashboard = getattr(get_dashboard_data_batched, "clear", None)
    if callable(clear_dashboard):
        clear_dashboard()

def clear_employees_cache():
    get_employees.clear()
    get_employee.clear()
    get_dashboard_data_batched.clear()


def create_job(payload):
    try:
        resp = httpx.post(f"{API_URL}/jobs", json=payload)
        if resp.status_code == 200:
            clear_jobs_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        return None

def update_job(job_id, payload):
    try:
        resp = httpx.put(f"{API_URL}/jobs/{job_id}", json=payload)
        if resp.status_code == 200:
            clear_jobs_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error updating job: {e}")
        return None

def delete_job(job_id):
    try:
        resp = httpx.delete(f"{API_URL}/jobs/{job_id}")
        if resp.status_code == 200:
            clear_jobs_cache()
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        return False

def archive_job(job_id):
    try:
        resp = httpx.post(f"{API_URL}/jobs/{job_id}/archive")
        if resp.status_code == 200:
            clear_jobs_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error archiving job: {e}")
        return None

def clone_job(job_id):
    try:
        resp = httpx.post(f"{API_URL}/jobs/{job_id}/clone")
        if resp.status_code == 200:
            clear_jobs_cache()
            return resp.json()
        return None
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

def upload_and_generate_jd(file_bytes, filename):
    try:
        files = {"file": (filename, file_bytes, "application/octet-stream")}
        resp = httpx.post(f"{API_URL}/jobs/upload-and-generate", files=files, timeout=90.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error generating JD from document: {e}")
        return None

def regenerate_jd(job_id, raw_text, current_draft):
    try:
        payload = {"raw_text": raw_text, "current_draft": current_draft}
        # If job_id is not yet created, we can just use 0
        resp = httpx.post(f"{API_URL}/jobs/{job_id}/regenerate", json=payload, timeout=90.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error regenerating JD: {e}")
        return None

def add_candidate_note(candidate_id, note):
    try:
        resp = httpx.post(f"{API_URL}/candidates/{candidate_id}/notes", params={"note": note})
        if resp.status_code == 200:
            clear_candidates_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error adding candidate note: {e}")
        return None

def update_candidate_status(candidate_id, status):
    try:
        resp = httpx.post(f"{API_URL}/candidates/{candidate_id}/status", params={"status": status})
        if resp.status_code == 200:
            clear_candidates_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error updating candidate status: {e}")
        return None

def upload_resume(file_bytes, filename):
    try:
        files = {"file": (filename, file_bytes, "application/octet-stream")}
        resp = httpx.post(f"{API_URL}/resumes/upload", files=files, timeout=90.0)
        if resp.status_code == 200:
            clear_candidates_cache()
            get_upload_history.clear()
            get_dashboard_data_batched.clear()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        return None

def parse_resume_text(text, filename="pasted_resume.txt"):
    try:
        resp = httpx.post(
            f"{API_URL}/resumes/parse-text",
            data={"text": text, "filename": filename},
            timeout=90.0,
        )
        if resp.status_code == 200:
            clear_candidates_cache()
            get_upload_history.clear()
            get_dashboard_data_batched.clear()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error parsing pasted resume text: {e}")
        return None

def screen_candidate_against_job(candidate_id, job_id):
    try:
        resp = httpx.get(f"{API_URL}/ai-screening", params={"candidate_id": candidate_id, "job_id": job_id}, timeout=90.0)
        if resp.status_code == 200:
            clear_candidates_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error screening candidate: {e}")
        return None

def approve_candidate(candidate_id):
    try:
        resp = httpx.post(f"{API_URL}/ai-screening/approve", params={"candidate_id": candidate_id})
        if resp.status_code == 200:
            clear_candidates_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error approving candidate: {e}")
        return None

def shortlist_candidate(candidate_id):
    try:
        resp = httpx.post(f"{API_URL}/ai-screening/shortlist", params={"candidate_id": candidate_id})
        if resp.status_code == 200:
            clear_candidates_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error shortlisting candidate: {e}")
        return None

def reject_candidate(candidate_id):
    try:
        resp = httpx.post(f"{API_URL}/ai-screening/reject", params={"candidate_id": candidate_id})
        if resp.status_code == 200:
            clear_candidates_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error rejecting candidate: {e}")
        return None

def schedule_interview(payload):
    try:
        resp = httpx.post(f"{API_URL}/interviews", json=payload, timeout=5.0)
        resp.raise_for_status()
        if resp.status_code == 200:
            clear_interviews_cache()
            clear_candidates_cache()
            return resp.json()
        return None
    except Exception as e:
        st.error(f"Failed to schedule interview: {e}")
        return None

@st.cache_data(ttl=30, show_spinner=False)
def get_interviews(candidate_id=None, job_id=None, status="All", round_name="All"):
    try:
        params = {"status": status, "round_name": round_name}
        if candidate_id: params["candidate_id"] = candidate_id
        if job_id: params["job_id"] = job_id
        resp = httpx.get(f"{API_URL}/interviews", params=params, timeout=5.0)
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []

def get_interview(interview_id):
    try:
        resp = httpx.get(f"{API_URL}/interviews/{interview_id}", timeout=5.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None

def update_interview(interview_id, payload):
    try:
        resp = httpx.put(f"{API_URL}/interviews/{interview_id}", json=payload, timeout=5.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None

def generate_interview_questions(interview_id, round_type, difficulty_level=None, number_of_questions=None, regenerate=False):
    """Generate questions, accepting the legacy (id, difficulty, count) call too."""
    if number_of_questions is None:
        # Legacy interview-management components did not expose a round type.
        number_of_questions = difficulty_level
        difficulty_level = round_type
        round_type = "Technical"

    try:
        payload = {"round_type": round_type, "difficulty_level": difficulty_level, "number_of_questions": number_of_questions, "regenerate": regenerate}
        resp = httpx.post(f"{API_URL}/interviews/{interview_id}/generate-questions", json=payload, timeout=40.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None

def add_interview_feedback(interview_id, feedback_payload):
    try:
        resp = httpx.post(f"{API_URL}/interviews/{interview_id}/feedback", json=feedback_payload, timeout=5.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None

def log_interview_decision(interview_id, decision):
    try:
        resp = httpx.put(f"{API_URL}/interviews/{interview_id}/decision", params={"decision": decision}, timeout=5.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None

def draft_interview_email(interview_id, email_mode):
    try:
        resp = httpx.post(f"{API_URL}/interviews/{interview_id}/generate-email", json={"email_mode": email_mode}, timeout=30.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None

def send_interview_email(interview_id, subject, body):
    try:
        resp = httpx.post(f"{API_URL}/interviews/{interview_id}/send-email", json={"subject": subject, "body": body}, timeout=5.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None

def get_interview_email_history(interview_id):
    try:
        resp = httpx.get(f"{API_URL}/interviews/{interview_id}/email-history", timeout=5.0)
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []

def update_interview_status(interview_id, status):
    try:
        resp = httpx.put(f"{API_URL}/interviews/{interview_id}/status", params={"status": status})
        if resp.status_code == 200:
            clear_interviews_cache()
            clear_candidates_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error updating interview status: {e}")
        return None

# --- EMPLOYEE OPERATIONS ---

def update_employee_details(employee_id, payload):
    try:
        resp = httpx.put(f"{API_URL}/employees/{employee_id}", json=payload)
        if resp.status_code == 200:
            clear_employees_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error updating employee: {e}")
        return None

def update_employee_skills(employee_id, payload):
    try:
        resp = httpx.put(f"{API_URL}/employees/{employee_id}/skills", json=payload)
        if resp.status_code == 200:
            clear_employees_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error updating employee skills: {e}")
        return None

def add_employee_project(employee_id, payload):
    try:
        resp = httpx.post(f"{API_URL}/employees/{employee_id}/projects", json=payload)
        if resp.status_code == 200:
            clear_employees_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error adding project: {e}")
        return None

def add_employee_performance(employee_id, payload):
    try:
        resp = httpx.post(f"{API_URL}/employees/{employee_id}/performance", json=payload)
        if resp.status_code == 200:
            clear_employees_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error adding performance: {e}")
        return None

def get_employee_performance_summary(employee_id):
    try:
        resp = httpx.get(f"{API_URL}/employees/{employee_id}/performance-summary")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        return None

def generate_talent_insights(employee_id):
    try:
        resp = httpx.post(f"{API_URL}/employees/{employee_id}/talent-insights", timeout=60.0)
        if resp.status_code == 200:
            clear_employees_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return None

def add_employee_note(employee_id, payload):
    try:
        resp = httpx.post(f"{API_URL}/employees/{employee_id}/notes", json=payload)
        if resp.status_code == 200:
            clear_employees_cache()
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Error adding employee note: {e}")
        return None

# --- REPORTS & EXPORT ---

def get_recruitment_summary(department="All"):
    try:
        resp = httpx.get(f"{API_URL}/reports/recruitment-summary", params={"department": department})
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error getting recruitment summary: {e}")
        return None

def get_job_report(job_id):
    try:
        resp = httpx.get(f"{API_URL}/reports/job/{job_id}")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error getting job report: {e}")
        return None

def get_candidate_report(candidate_id):
    try:
        resp = httpx.get(f"{API_URL}/reports/candidate/{candidate_id}")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error getting candidate report: {e}")
        return None

def get_employee_report(employee_id):
    try:
        resp = httpx.get(f"{API_URL}/reports/employee/{employee_id}")
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error getting employee report: {e}")
        return None

def generate_custom_report(entity, filters, fields, group_by=""):
    try:
        payload = {"entity": entity, "filters": filters, "fields": fields, "group_by": group_by}
        resp = httpx.post(f"{API_URL}/reports/custom", json=payload)
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error generating custom report: {e}")
        return []

def trigger_export(report_type, format_type, payload):
    try:
        data = {"report_type": report_type, "format": format_type, "payload": payload}
        resp = httpx.post(f"{API_URL}/reports/export", json=data)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error triggering export: {e}")
        return None

def check_export_status(export_id):
    try:
        resp = httpx.get(f"{API_URL}/reports/export/{export_id}/status")
        if resp.status_code == 200:
            return resp.json().get("status")
        return "failed"
    except Exception as e:
        logger.error(f"Error checking export status: {e}")
        return "failed"

# --- ANALYTICS DASHBOARD ---

@st.cache_data(ttl=60, show_spinner=False)
def get_analytics_bundle(department="All", days=30):
    try:
        resp = httpx.get(f"{API_URL}/analytics/dashboard-bundle", params={"department": department, "days": days}, timeout=30.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error getting analytics bundle: {e}")
        return None

def refresh_analytics():
    get_analytics_bundle.clear()
    try:
        httpx.get(f"{API_URL}/analytics/refresh")
    except Exception:
        pass

# --- AI COPILOT ---

def chat_with_copilot(session_id, message):
    try:
        resp = httpx.post(f"{API_URL}/copilot/chat", json={"session_id": session_id, "message": message}, timeout=60.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error chatting with copilot: {e}")
        return None

def confirm_copilot_action(session_id, action_type, action_payload):
    try:
        resp = httpx.post(f"{API_URL}/copilot/action/confirm", json={
            "session_id": session_id,
            "action_type": action_type,
            "action_payload": action_payload
        })
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error confirming copilot action: {e}")
        return None

def get_copilot_suggestions():
    try:
        resp = httpx.get(f"{API_URL}/copilot/suggestions")
        return resp.json().get("suggestions", []) if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error getting copilot suggestions: {e}")
        return []
