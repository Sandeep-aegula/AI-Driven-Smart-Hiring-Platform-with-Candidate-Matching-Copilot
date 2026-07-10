"""
services/json_storage.py — HirePilot Cached JSON Storage
==========================================================
Direct JSON storage read/write with st.cache_data caching.
Bypasses the FastAPI backend for read-only queries that need
to be fast (e.g., dashboard stats, analytics charts).

For writes, always use the api_client so the backend stays in sync.
"""

import json
import os
import streamlit as st
from typing import Any

# Resolve storage.json path relative to this file
_STORAGE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "storage.json")
)


@st.cache_data(ttl=60, show_spinner=False)
def load_storage() -> dict:
    """Load the entire storage.json file. Cached for 60 seconds."""
    try:
        with open(_STORAGE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"jobs": [], "candidates": [], "interviews": [], "employees": [],
                "uploads": [], "skills": []}


@st.cache_data(ttl=60, show_spinner=False)
def get_all_jobs() -> list:
    return load_storage().get("jobs", [])


@st.cache_data(ttl=60, show_spinner=False)
def get_all_candidates() -> list:
    return load_storage().get("candidates", [])


@st.cache_data(ttl=60, show_spinner=False)
def get_all_interviews() -> list:
    return load_storage().get("interviews", [])


@st.cache_data(ttl=60, show_spinner=False)
def get_all_employees() -> list:
    return load_storage().get("employees", [])


@st.cache_data(ttl=60, show_spinner=False)
def get_dashboard_stats() -> dict:
    """Aggregate KPI stats for the Dashboard. Cached for 60 seconds."""
    data = load_storage()
    jobs = data.get("jobs", [])
    candidates = data.get("candidates", [])
    interviews = data.get("interviews", [])
    employees = data.get("employees", [])

    total_jobs = len(jobs)
    active_jobs = sum(1 for j in jobs if j.get("status") == "Open")
    total_candidates = len(candidates)
    shortlisted = sum(1 for c in candidates if c.get("status") == "Shortlisted")
    interviews_scheduled = sum(1 for i in interviews if i.get("status") in ("Scheduled", "Confirmed"))
    hired = sum(1 for c in candidates if c.get("status") == "Hired")

    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_candidates": total_candidates,
        "shortlisted": shortlisted,
        "interviews_scheduled": interviews_scheduled,
        "hired": hired,
        "total_employees": len(employees),
    }


def invalidate_all():
    """Call after any write to bust all storage caches."""
    load_storage.clear()
    get_all_jobs.clear()
    get_all_candidates.clear()
    get_all_interviews.clear()
    get_all_employees.clear()
    get_dashboard_stats.clear()
