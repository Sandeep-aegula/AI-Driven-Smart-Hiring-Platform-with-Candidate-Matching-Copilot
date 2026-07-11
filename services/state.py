"""
services/state.py — HirePilot Global Session State Manager
===========================================================
Single source of truth for ALL session state keys.
Call `init_state()` once at the top of app.py.

Navigation is driven entirely by st.session_state["current_page"].
Never use st.switch_page() — just set current_page and st.rerun().
"""

import streamlit as st
from typing import Any, Optional


# ── Default values for every key used in the application ────────────────────

_DEFAULTS: dict = {
    # ── Navigation ────────────────────────────────────────────────────────
    "current_page": "Dashboard",

    # ── Jobs ──────────────────────────────────────────────────────────────
    "selected_job_id": None,
    "job_action": "list",          # "list" | "create" | "edit" | "view"
    "generated_jd_data": None,

    # ── Candidates ────────────────────────────────────────────────────────
    "selected_cand_id": None,
    "selected_eval_cand_id": None,  # cross-page pre-select for AI Screening

    # ── Resume Parser ─────────────────────────────────────────────────────
    "selected_resume_id": None,

    # ── Interviews ────────────────────────────────────────────────────────
    "selected_interview_id": None,
    "generated_questions": None,

    # ── Employees ─────────────────────────────────────────────────────────
    "selected_employee_id": None,

    # ── AI Copilot ────────────────────────────────────────────────────────
    "messages": [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm HirePilot's AI Copilot, running locally on "
                "`qwen2.5-coder:7b`. Select a quick action below or ask me "
                "any recruitment questions."
            ),
        }
    ],

    # ── Reports ───────────────────────────────────────────────────────────
    "reports_history": [
        {"filename": "Hiring_Report_Q2_2026.pdf",    "type": "Hiring Report",    "time": "3 hours ago"},
        {"filename": "Candidate_Roster_Jul_2026.csv", "type": "Candidate Report", "time": "2 days ago"},
        {"filename": "Interview_Logs_Jul_2026.xlsx",  "type": "Interview Report", "time": "3 days ago"},
    ],
    "generated_report_type": None,

    # ── Search / Filters ──────────────────────────────────────────────────
    "search_query": "",
    "jobs_search": "",
    "jobs_department": "All",
    "jobs_status": "All",
    "cand_search": "",
    "cand_status": "All",
    "cand_skill": "All",
    "emp_search": "",
    "emp_dept": "All",

    # ── Theme ─────────────────────────────────────────────────────────────
    "theme": "light",

    # ── AI response cache (persists screening results across reruns) ───────
    "ai_responses": {},

    # ── CSS injection sentinel ─────────────────────────────────────────────
    "__css_injected__": False,
}


def init_state() -> None:
    """
    Initialise every session state key with its default value.
    Safe to call on every rerun — only sets keys that don't exist yet.
    """
    for key, default in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


# ── Navigation helpers ───────────────────────────────────────────────────────

def navigate_to(page: str) -> None:
    """Set current_page and trigger a rerun.  Replaces st.switch_page()."""
    st.session_state["current_page"] = page
    st.rerun()


def current_page() -> str:
    return st.session_state.get("current_page", "Dashboard")


# ── Generic typed helpers ────────────────────────────────────────────────────

def get(key: str, default: Any = None) -> Any:
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    st.session_state[key] = value
