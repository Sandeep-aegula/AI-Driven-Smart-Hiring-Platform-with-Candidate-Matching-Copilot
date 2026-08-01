"""Test the Candidate Management shortlist workflow."""
import httpx
import json

BASE = "http://localhost:8000"

# Test 1: Get candidates for job 7
resp = httpx.get(f"{BASE}/candidates", params={"job_id": 7, "status": "All", "limit": 100})
print(f"GET /candidates status: {resp.status_code}")
data = resp.json()
items = data.get("items", [])
print(f"Candidates returned: {len(items)}")
for item in items:
    print(f"  - ID: {item.get('id')}, App ID: {item.get('application_id')}, Name: {item.get('name')}, Status: {item.get('status')}")

# Test 2: Get pending communications
resp2 = httpx.get(f"{BASE}/communications/pending")
print(f"\nGET /communications/pending status: {resp2.status_code}")
comms = resp2.json()
print(f"Pending communications: {len(comms)}")
for comm in comms:
    print(f"  - App ID: {comm.get('application_id')}, Candidate: {comm.get('candidate_name')}, Status: {comm.get('status')}")

# Test 3: Check if there are any applications with status 'shortlisted'
# First get all candidates to find application IDs
if items:
    # Try to shortlist the first candidate
    app_id = items[0].get("application_id")
    if app_id:
        print(f"\n--- Testing bulk shortlist with application_id={app_id} ---")
        payload = [app_id]
        resp3 = httpx.post(f"{BASE}/candidates/applications/shortlist-bulk", json=payload)
        print(f"POST /candidates/applications/shortlist-bulk status: {resp3.status_code}")
        result = resp3.json()
        print(f"Response: {json.dumps(result, indent=2)}")

        # Test 4: Verify candidate is removed from list
        resp4 = httpx.get(f"{BASE}/candidates", params={"job_id": 7, "status": "All", "limit": 100})
        data4 = resp4.json()
        items4 = data4.get("items", [])
        print(f"\nAfter shortlist - Candidates returned: {len(items4)}")
        for item in items4:
            print(f"  - ID: {item.get('id')}, App ID: {item.get('application_id')}, Name: {item.get('name')}, Status: {item.get('status')}")

        # Test 5: Verify communication was created
        resp5 = httpx.get(f"{BASE}/communications/pending")
        comms5 = resp5.json()
        print(f"\nAfter shortlist - Pending communications: {len(comms5)}")
        for comm in comms5:
            print(f"  - App ID: {comm.get('application_id')}, Candidate: {comm.get('candidate_name')}")
else:
    print("\nNo candidates found to test shortlist")
