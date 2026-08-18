from backend.database.data_store import data_store

async def get_system_context() -> str:
    """
    Returns a summarized string of the system's current state to be injected into the LLM prompt.
    Truncates lists to prevent context window overflow.
    """
    jobs = await data_store.list_jobs()
    cands = await data_store.list_candidates()
    ivs = await data_store.list_interviews()
    emps = await data_store.list_employees()

    # Summarize Jobs
    active_jobs = [j for j in jobs if j.get("status") == "Active"]
    jobs_summary = ", ".join([f"{j.get('id')}: {j.get('title')} ({j.get('department')})" for j in active_jobs[:10]])
    if len(active_jobs) > 10:
        jobs_summary += f" and {len(active_jobs) - 10} more."

    # Summarize Candidates
    active_cands = [c for c in cands if c.get("status") not in ("Hired", "Rejected")]
    cands_summary = ", ".join([f"{c.get('id')}: {c.get('name')} (Score: {c.get('match_score')}, Status: {c.get('status')})" for c in active_cands[:10]])
    if len(active_cands) > 10:
        cands_summary += f" and {len(active_cands) - 10} more."

    # Summarize Interviews
    ivs_summary = f"{len(ivs)} total interviews scheduled."

    # Summarize Employees
    emps_summary = f"{len(emps)} total employees."

    return f"""
    CURRENT SYSTEM CONTEXT:
    Active Jobs: {jobs_summary or 'None'}
    Active Candidates: {cands_summary or 'None'}
    Interviews: {ivs_summary}
    Employees: {emps_summary}
    """
