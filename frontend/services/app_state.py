"""
services/app_state.py — HirePilot Global State Manager
=========================================================
Single source of truth for all session state.

Usage in pages:
    from frontend.services.app_state import AppState
    AppState.init()
    AppState.set_selected_job("job-123")
    job_id = AppState.selected_job
"""

import streamlit as st
from typing import Any, Optional


class AppState:
    """
    Centralized session state manager.
    All keys are namespaced under __hp__ to avoid collisions with Streamlit internals.
    """

    # ------------------------------------------------------------------ #
    #  Initialise defaults once per browser session                        #
    # ------------------------------------------------------------------ #

    DEFAULTS = {
        # Navigation
        "current_page": "Dashboard",

        # Jobs
        "selected_job_id": None,
        "job_action": "list",
        "generated_jd_data": None,

        # Candidates
        "selected_cand_id": None,

        # Resume
        "selected_resume_id": None,

        # Interviews
        "selected_interview_id": None,
        "generated_questions": None,

        # Employees
        "selected_employee_id": None,

        # AI Copilot
        "messages": [],

        # Reports
        "reports_history": [],

        # Filters (persist across pages)
        "jobs_search": "",
        "jobs_department": "All",
        "jobs_status": "All",
        "cand_search": "",
        "cand_status": "All",
        "cand_skill": "All",
        "emp_search": "",
        "emp_dept": "All",

        # Theme
        "theme": "dark",

        # AI responses cache
        "ai_responses": {},

        # CSS sentinel (managed by cache.py)
        "__css_injected__": False,
    }

    @classmethod
    def init(cls):
        """Ensure all state keys exist with their default values.
        Safe to call on every page — only initialises missing keys.
        """
        for key, default in cls.DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = default

    # ------------------------------------------------------------------ #
    #  Typed getters / setters                                             #
    # ------------------------------------------------------------------ #

    # --- Jobs ---
    @classmethod
    @property
    def selected_job_id(cls) -> Optional[str]:
        return st.session_state.get("selected_job_id")

    @classmethod
    def set_selected_job(cls, job_id: Optional[str]):
        st.session_state["selected_job_id"] = job_id

    @classmethod
    def set_job_action(cls, action: str):
        st.session_state["job_action"] = action

    # --- Candidates ---
    @classmethod
    @property
    def selected_cand_id(cls) -> Optional[str]:
        return st.session_state.get("selected_cand_id")

    @classmethod
    def set_selected_candidate(cls, cand_id: Optional[str]):
        st.session_state["selected_cand_id"] = cand_id

    # --- Interviews ---
    @classmethod
    def set_selected_interview(cls, iview_id: Optional[str]):
        st.session_state["selected_interview_id"] = iview_id

    # --- Employees ---
    @classmethod
    def set_selected_employee(cls, emp_id: Optional[str]):
        st.session_state["selected_employee_id"] = emp_id

    # --- AI Copilot messages ---
    @classmethod
    def add_message(cls, role: str, content: str):
        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        st.session_state["messages"].append({"role": role, "content": content})

    @classmethod
    def clear_messages(cls):
        st.session_state["messages"] = []

    # --- AI responses (cache screening results across reruns) ---
    @classmethod
    def get_ai_response(cls, key: str) -> Optional[Any]:
        return st.session_state.get("ai_responses", {}).get(key)

    @classmethod
    def set_ai_response(cls, key: str, value: Any):
        if "ai_responses" not in st.session_state:
            st.session_state["ai_responses"] = {}
        st.session_state["ai_responses"][key] = value

    # --- Reports history ---
    @classmethod
    def add_report(cls, report: dict):
        if "reports_history" not in st.session_state:
            st.session_state["reports_history"] = []
        st.session_state["reports_history"].insert(0, report)

    # --- Generic get/set ---
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        return st.session_state.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any):
        st.session_state[key] = value
