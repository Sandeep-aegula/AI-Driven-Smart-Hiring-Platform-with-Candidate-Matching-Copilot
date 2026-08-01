filepath = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\frontend\components\api_client.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# The corrupted section - shortlist_bulk is missing its body and update_job is nested inside it
old_corrupted = '''def shortlist_bulk(application_ids: list[int]):
    """Bulk shortlist multiple candidates by their application IDs."""
    try:
        resp = httpx.post(
            f"{API_URL}/candidates/applications/shortlist-bulk",
            json=application_ids,
            timeout=30.0,
        )
        if resp.status_code in (200, 207):
            def update_job(job_id, payload):'''

new_fixed = '''def shortlist_bulk(application_ids: list[int]):
    """Bulk shortlist multiple candidates by their application IDs."""
    try:
        resp = httpx.post(
            f"{API_URL}/candidates/applications/shortlist-bulk",
            json=application_ids,
            timeout=30.0,
        )
        if resp.status_code in (200, 207):
            clear_candidates_cache()
            return resp.json()
        logger.error(f"Bulk shortlist failed with status {resp.status_code}: {resp.text}")
        return None
    except Exception as e:
        logger.error(f"Error bulk shortlisting: {e}")
        return None

def update_job(job_id, payload):'''

if old_corrupted in content:
    content = content.replace(old_corrupted, new_fixed, 1)
    print("Fixed shortlist_bulk function")
else:
    print("ERROR: Could not find corrupted section")
    idx = content.find('def shortlist_bulk')
    if idx >= 0:
        print(f"Found at {idx}: {repr(content[idx:idx+200])}")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
