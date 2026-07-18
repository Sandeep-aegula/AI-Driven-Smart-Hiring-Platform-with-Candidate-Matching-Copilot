import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def get_pipeline_funnel(jobs_data: list[dict], applications_data: list[dict], interviews_data: list[dict], candidates_data: list[dict], department_filter: str = "All") -> dict:
    """
    Computes funnel counts: Applied -> Screened -> Interview -> Offer -> Hired.
    """
    if not jobs_data:
        return {"Applied": 0, "Screened": 0, "Interview": 0, "Offer": 0, "Hired": 0}

    df_jobs = pd.DataFrame(jobs_data)
    if department_filter != "All":
        df_jobs = df_jobs[df_jobs["department"] == department_filter]
        
    valid_job_ids = set(df_jobs["id"].tolist()) if not df_jobs.empty else set()
    
    if not valid_job_ids:
        return {"Applied": 0, "Screened": 0, "Interview": 0, "Offer": 0, "Hired": 0}

    # Applied (From applications_data)
    df_apps = pd.DataFrame(applications_data) if applications_data else pd.DataFrame()
    applied = 0
    if not df_apps.empty and "job_id" in df_apps.columns:
        applied = int(df_apps[df_apps["job_id"].isin(valid_job_ids)].shape[0])

    # Screened (Candidates linked to valid jobs with status != New)
    df_cands = pd.DataFrame(candidates_data) if candidates_data else pd.DataFrame()
    screened = 0
    hired = 0
    offer = 0
    interview_status = 0
    
    if not df_cands.empty:
        # We need a way to link candidate to job. Let's assume apps link them.
        if not df_apps.empty:
            valid_cands = set(df_apps[df_apps["job_id"].isin(valid_job_ids)]["candidate_id"])
            df_cands = df_cands[df_cands["id"].isin(valid_cands)]
            
            screened = int(df_cands[df_cands["status"] != "New"].shape[0])
            hired = int(df_cands[df_cands["status"] == "Hired"].shape[0])
            offer = int(df_cands[df_cands["status"] == "Offer"].shape[0])
            interview_status = int(df_cands[df_cands["status"] == "Interview"].shape[0])
    
    # Interview (From interviews_data)
    df_iv = pd.DataFrame(interviews_data) if interviews_data else pd.DataFrame()
    interview_count = 0
    if not df_iv.empty and "job_id" in df_iv.columns:
        # Distinct candidates interviewed
        df_iv_valid = df_iv[df_iv["job_id"].isin(valid_job_ids)]
        if not df_iv_valid.empty:
            interview_count = int(df_iv_valid["candidate_id"].nunique())
            
    # Max of status-based or interview table based
    actual_interview = max(interview_status, interview_count, hired + offer)
    actual_offer = max(offer, hired)

    return {
        "Applied": applied,
        "Screened": max(screened, actual_interview),
        "Interview": actual_interview,
        "Offer": actual_offer,
        "Hired": hired
    }

def get_hiring_velocity(applications_data: list[dict], interviews_data: list[dict], candidates_data: list[dict], days: int = 30) -> list[dict]:
    """
    Returns time-series (weekly/daily) of apps, interviews, and hires.
    """
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()
    
    # Generate date range
    date_range = pd.date_range(start=cutoff_date, end=datetime.utcnow().date())
    df_dates = pd.DataFrame(date_range, columns=["date"])
    df_dates["date_str"] = df_dates["date"].dt.strftime("%Y-%m-%d")
    
    # Applications
    df_apps = pd.DataFrame(applications_data) if applications_data else pd.DataFrame()
    app_counts = {}
    if not df_apps.empty and "created_at" in df_apps.columns:
        df_apps["date"] = pd.to_datetime(df_apps["created_at"]).dt.strftime("%Y-%m-%d")
        app_counts = df_apps.groupby("date").size().to_dict()
        
    # Interviews
    df_iv = pd.DataFrame(interviews_data) if interviews_data else pd.DataFrame()
    iv_counts = {}
    if not df_iv.empty and "date" in df_iv.columns:
        iv_counts = df_iv.groupby("date").size().to_dict()
        
    # Hires
    df_cands = pd.DataFrame(candidates_data) if candidates_data else pd.DataFrame()
    hire_counts = {}
    if not df_cands.empty and "updated_at" in df_cands.columns and "status" in df_cands.columns:
        df_hires = df_cands[df_cands["status"] == "Hired"].copy()
        if not df_hires.empty:
            df_hires["date"] = pd.to_datetime(df_hires["updated_at"]).dt.strftime("%Y-%m-%d")
            hire_counts = df_hires.groupby("date").size().to_dict()

    result = []
    for d in df_dates["date_str"]:
        result.append({
            "date": d,
            "Applications": app_counts.get(d, 0),
            "Interviews": iv_counts.get(d, 0),
            "Hires": hire_counts.get(d, 0)
        })
        
    return result

def get_source_quality(candidates_data: list[dict], applications_data: list[dict], jobs_data: list[dict], department_filter: str = "All") -> dict:
    """
    Match-score distribution and hire-rate.
    """
    df_cands = pd.DataFrame(candidates_data) if candidates_data else pd.DataFrame()
    if df_cands.empty:
        return {"avg_score": 0, "distribution": {}, "hire_rate": 0}
        
    df_jobs = pd.DataFrame(jobs_data) if jobs_data else pd.DataFrame()
    if department_filter != "All" and not df_jobs.empty:
        df_jobs = df_jobs[df_jobs["department"] == department_filter]
        valid_job_ids = set(df_jobs["id"].tolist())
        
        df_apps = pd.DataFrame(applications_data) if applications_data else pd.DataFrame()
        if not df_apps.empty:
            valid_cands = set(df_apps[df_apps["job_id"].isin(valid_job_ids)]["candidate_id"])
            df_cands = df_cands[df_cands["id"].isin(valid_cands)]
            
    if df_cands.empty:
        return {"avg_score": 0, "distribution": {}, "hire_rate": 0}

    avg_score = float(df_cands["match_score"].mean()) if "match_score" in df_cands.columns else 0
    
    # Bins: 0-20, 21-40, 41-60, 61-80, 81-100
    dist = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    if "match_score" in df_cands.columns:
        for score in df_cands["match_score"].fillna(0):
            if score <= 20: dist["0-20"] += 1
            elif score <= 40: dist["21-40"] += 1
            elif score <= 60: dist["41-60"] += 1
            elif score <= 80: dist["61-80"] += 1
            else: dist["81-100"] += 1
            
    hire_rate = 0
    if "status" in df_cands.columns:
        hired = len(df_cands[df_cands["status"] == "Hired"])
        total = len(df_cands)
        hire_rate = round((hired / total) * 100, 1) if total > 0 else 0
        
    return {
        "avg_score": round(avg_score, 1),
        "distribution": dist,
        "hire_rate": hire_rate
    }

def get_interview_load(interviews_data: list[dict], days: int = 14) -> list[dict]:
    """
    Heatmap data: dates vs interview counts.
    """
    df_iv = pd.DataFrame(interviews_data) if interviews_data else pd.DataFrame()
    if df_iv.empty or "date" not in df_iv.columns:
        return []
        
    today = datetime.utcnow().date()
    end_date = today + timedelta(days=days)
    
    df_iv["date_obj"] = pd.to_datetime(df_iv["date"], errors="coerce").dt.date
    df_filtered = df_iv[(df_iv["date_obj"] >= today) & (df_iv["date_obj"] <= end_date)]
    
    if df_filtered.empty:
        return []
        
    counts = df_filtered.groupby("date").size().reset_index(name="count")
    return counts.to_dict(orient="records")

def get_workforce_summary(employees_data: list[dict]) -> dict:
    """
    Headcount by dept, average performance, talent rating dist.
    """
    df_emp = pd.DataFrame(employees_data) if employees_data else pd.DataFrame()
    if df_emp.empty:
        return {"headcount": 0, "by_department": {}, "avg_performance": 0, "ratings": {}}
        
    headcount = len(df_emp)
    by_dept = df_emp.groupby("department").size().to_dict() if "department" in df_emp.columns else {}
    
    # Aggregate performance
    total_perf = 0
    perf_count = 0
    ratings = {}
    
    if "performance_history" in df_emp.columns:
        for hist in df_emp["performance_history"]:
            if isinstance(hist, list) and hist:
                avg = sum(h.get("kpi_score", 0) for h in hist) / len(hist)
                total_perf += avg
                perf_count += 1
                
    avg_performance = round(total_perf / perf_count, 1) if perf_count > 0 else 0
    
    if "talent_insights" in df_emp.columns:
        for ti in df_emp["talent_insights"]:
            if isinstance(ti, dict) and "rating" in ti:
                r = ti["rating"]
                ratings[r] = ratings.get(r, 0) + 1
                
    return {
        "headcount": headcount,
        "by_department": by_dept,
        "avg_performance": avg_performance,
        "ratings": ratings
    }

def get_overview_kpis(jobs_data: list[dict], candidates_data: list[dict], interviews_data: list[dict]) -> dict:
    df_jobs = pd.DataFrame(jobs_data) if jobs_data else pd.DataFrame()
    df_cands = pd.DataFrame(candidates_data) if candidates_data else pd.DataFrame()
    df_iv = pd.DataFrame(interviews_data) if interviews_data else pd.DataFrame()
    
    open_roles = int(df_jobs[df_jobs["status"] == "Active"].shape[0]) if not df_jobs.empty and "status" in df_jobs.columns else 0
    active_cands = int(df_cands[~df_cands["status"].isin(["Hired", "Rejected"])].shape[0]) if not df_cands.empty and "status" in df_cands.columns else 0
    
    # Interviews this week
    iv_this_week = 0
    if not df_iv.empty and "date" in df_iv.columns:
        df_iv["date_obj"] = pd.to_datetime(df_iv["date"], errors="coerce").dt.date
        today = datetime.utcnow().date()
        week_end = today + timedelta(days=7)
        iv_this_week = int(df_iv[(df_iv["date_obj"] >= today) & (df_iv["date_obj"] <= week_end)].shape[0])
        
    avg_match = round(float(df_cands["match_score"].mean()), 1) if not df_cands.empty and "match_score" in df_cands.columns else 0
    
    return {
        "open_roles": open_roles,
        "active_candidates": active_cands,
        "interviews_this_week": iv_this_week,
        "average_match_score": avg_match
    }
