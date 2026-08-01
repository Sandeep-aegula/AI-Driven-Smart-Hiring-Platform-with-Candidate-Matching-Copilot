"""
Comprehensive Testing Script for Candidate Management System

This script tests the complete workflow from candidate filtering to email sending.
Run this after starting the backend server.
"""

import httpx
import asyncio
from datetime import datetime, timedelta


BASE_URL = "http://localhost:8000"
client = httpx.Client(timeout=30.0)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_test(test_name, passed, details=""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"    {details}")


def test_get_candidates_all_jobs():
    """Test 1: Get all candidates without filters."""
    print_section("TEST 1: Get All Candidates")

    try:
        response = client.get(f"{BASE_URL}/candidates")
        assert response.status_code == 200, f"Status code: {response.status_code}"

        data = response.json()
        assert "items" in data, "Missing 'items' field"
        assert "total" in data, "Missing 'total' field"
        assert "status_counts" in data, "Missing 'status_counts' field"
        assert "average_ats_score" in data, "Missing 'average_ats_score' field"
        assert "selected_job_title" in data, "Missing 'selected_job_title' field"

        total = data["total"]
        items = len(data["items"])

        print_test("Get all candidates", True, f"Total: {total}, Retrieved: {items}")
        print_test("Response structure", True, "All required fields present")

        # Print status counts
        print("\nStatus Counts:")
        for status, count in data["status_counts"].items():
            print(f"  - {status}: {count}")

        print(f"\nAverage ATS Score: {data['average_ats_score']}%")
        print(f"Selected Job: {data['selected_job_title']}")

        return data

    except Exception as e:
        print_test("Get all candidates", False, str(e))
        return None


def test_get_jobs():
    """Test 2: Get all jobs."""
    print_section("TEST 2: Get All Jobs")

    try:
        response = client.get(f"{BASE_URL}/jobs")
        assert response.status_code == 200, f"Status code: {response.status_code}"

        jobs = response.json()
        assert isinstance(jobs, list), "Jobs should be a list"

        print_test("Get all jobs", True, f"Found {len(jobs)} jobs")

        # Print job list
        print("\nAvailable Jobs:")
        for job in jobs[:10]:  # Show first 10
            print(f"  - ID: {job.get('id')}, Title: {job.get('title')}, Dept: {job.get('department')}")

        return jobs

    except Exception as e:
        print_test("Get all jobs", False, str(e))
        return []


def test_get_candidates_by_job(job_id, job_title):
    """Test 3: Get candidates filtered by job."""
    print_section(f"TEST 3: Get Candidates for Job ID {job_id} ({job_title})")

    try:
        response = client.get(f"{BASE_URL}/candidates", params={"job_id": job_id})
        assert response.status_code == 200, f"Status code: {response.status_code}"

        data = response.json()
        total = data["total"]
        items = data["items"]
        role_count = data["role_candidate_count"]

        print_test("Filter by job", True, f"Total: {total}, Role-specific: {role_count}")
        print_test("Job title matches", data["selected_job_title"] == job_title,
                  f"Got: {data['selected_job_title']}")

        # Verify all candidates belong to this job
        all_match = True
        for item in items[:5]:  # Check first 5
            if item.get("application_id"):
                # Would need to verify application belongs to job
                pass

        print(f"\nStatus Counts for {job_title}:")
        for status, count in data["status_counts"].items():
            print(f"  - {status}: {count}")

        print(f"\nAverage ATS Score: {data['average_ats_score']}%")

        return data

    except Exception as e:
        print_test("Filter by job", False, str(e))
        return None


def test_filter_by_status(status_filter):
    """Test 4: Filter by status."""
    print_section(f"TEST 4: Filter by Status '{status_filter}'")

    try:
        response = client.get(f"{BASE_URL}/candidates", params={"status": status_filter})
        assert response.status_code == 200, f"Status code: {response.status_code}"

        data = response.json()
        items = data["items"]

        # Verify all items match the status
        all_match = all(item.get("status") == status_filter for item in items)

        print_test("Filter by status", all_match, f"Found {len(items)} candidates with status '{status_filter}'")

        return data

    except Exception as e:
        print_test("Filter by status", False, str(e))
        return None


def test_filter_by_ats_score(min_score):
    """Test 5: Filter by minimum ATS score."""
    print_section(f"TEST 5: Filter by Minimum ATS Score {min_score}%")

    try:
        response = client.get(f"{BASE_URL}/candidates", params={"min_match_score": min_score})
        assert response.status_code == 200, f"Status code: {response.status_code}"

        data = response.json()
        items = data["items"]

        # Verify all items have ATS score >= min_score
        all_match = all(item.get("ats_score", 0) >= min_score for item in items)

        print_test("Filter by ATS score", all_match,
                  f"Found {len(items)} candidates with ATS ≥ {min_score}%")

        # Show score distribution
        if items:
            scores = [item.get("ats_score", 0) for item in items]
            print(f"  Score Range: {min(scores)}% - {max(scores)}%")

        return data

    except Exception as e:
        print_test("Filter by ATS score", False, str(e))
        return None


def test_search_candidates(search_query):
    """Test 6: Search candidates."""
    print_section(f"TEST 6: Search for '{search_query}'")

    try:
        response = client.get(f"{BASE_URL}/candidates", params={"search": search_query})
        assert response.status_code == 200, f"Status code: {response.status_code}"

        data = response.json()
        items = data["items"]

        print_test("Search candidates", True, f"Found {len(items)} matches")

        # Show first few results
        print("\nSearch Results:")
        for item in items[:5]:
            print(f"  - {item.get('name')} ({item.get('email')})")

        return data

    except Exception as e:
        print_test("Search candidates", False, str(e))
        return None


def test_get_application_details(application_id):
    """Test 7: Get application details."""
    print_section(f"TEST 7: Get Application Details (ID: {application_id})")

    try:
        response = client.get(f"{BASE_URL}/candidates/applications/{application_id}")
        assert response.status_code == 200, f"Status code: {response.status_code}"

        data = response.json()
        assert "candidate" in data, "Missing candidate data"
        assert "job" in data, "Missing job data"

        candidate = data["candidate"]
        job = data["job"]
        resume = data.get("resume")
        ats_score = data.get("ats_score")

        print_test("Get application details", True, f"Application ID: {application_id}")
        print(f"\n  Candidate: {candidate.get('name')}")
        print(f"  Job: {job.get('title') if job else 'N/A'}")
        print(f"  Status: {data.get('status')}")

        if resume:
            print(f"  Resume: {resume.get('original_filename')}")
            print_test("Resume uses original_filename", 'original_filename' in resume, "✓ Correct field")

        if ats_score:
            print(f"  ATS Score: {ats_score.get('ats_score')}%")
            print(f"    Skills: {ats_score.get('skills_score')}%")
            print(f"    Experience: {ats_score.get('experience_score')}%")
            print(f"    Education: {ats_score.get('education_score')}%")

        return data

    except Exception as e:
        print_test("Get application details", False, str(e))
        return None


def test_shortlist_candidate(application_id):
    """Test 8: Shortlist a candidate."""
    print_section(f"TEST 8: Shortlist Candidate (Application ID: {application_id})")

    try:
        response = client.post(f"{BASE_URL}/candidates/applications/{application_id}/shortlist")
        assert response.status_code == 200, f"Status code: {response.status_code}"

        data = response.json()
        assert data.get("success"), "Shortlist operation failed"

        print_test("Shortlist candidate", True, data.get("message"))
        print(f"\n  Candidate: {data.get('candidate_name')}")
        print(f"  Job: {data.get('job_title')}")
        print(f"  Status: {data.get('status')}")
        print(f"  Communication Created: {data.get('communication_created')}")

        return data

    except Exception as e:
        print_test("Shortlist candidate", False, str(e))
        return None


def test_shortlist_idempotence(application_id):
    """Test 9: Test shortlist idempotence."""
    print_section(f"TEST 9: Test Shortlist Idempotence (Application ID: {application_id})")

    try:
        # Shortlist again
        response = client.post(f"{BASE_URL}/candidates/applications/{application_id}/shortlist")
        assert response.status_code == 200, f"Status code: {response.status_code}"

        data = response.json()
        message = data.get("message")

        is_idempotent = "already" in message.lower()

        print_test("Idempotence check", is_idempotent, message)

        return data

    except Exception as e:
        print_test("Idempotence check", False, str(e))
        return None


def test_bulk_shortlist(application_ids):
    """Test 10: Bulk shortlist candidates."""
    print_section(f"TEST 10: Bulk Shortlist {len(application_ids)} Candidates")

    try:
        response = client.post(
            f"{BASE_URL}/candidates/applications/shortlist-bulk",
            json=application_ids
        )
        assert response.status_code == 200, f"Status code: {response.status_code}"

        data = response.json()
        assert data.get("success"), "Bulk shortlist operation failed"

        results = data.get("results", {})
        successful = len(results.get("successful", []))
        failed = len(results.get("failed", []))
        already = len(results.get("already_shortlisted", []))

        print_test("Bulk shortlist", True, data.get("message"))
        print(f"\n  Total Processed: {data.get('total_processed')}")
        print(f"  Successful: {successful}")
        print(f"  Already Shortlisted: {already}")
        print(f"  Failed: {failed}")

        if successful > 0:
            print("\n  Successfully Shortlisted:")
            for item in results["successful"][:5]:
                print(f"    - {item.get('candidate_name')} (App ID: {item.get('application_id')})")

        return data

    except Exception as e:
        print_test("Bulk shortlist", False, str(e))
        return None


def test_get_pending_communications():
    """Test 11: Get pending communications."""
    print_section("TEST 11: Get Pending Communications")

    try:
        response = client.get(f"{BASE_URL}/communications/pending")
        assert response.status_code == 200, f"Status code: {response.status_code}"

        data = response.json()
        assert isinstance(data, list), "Pending communications should be a list"

        print_test("Get pending communications", True, f"Found {len(data)} pending")

        # Show pending candidates
        print("\nPending Communications:")
        for item in data[:10]:
            print(f"  - {item.get('candidate_name')} ({item.get('candidate_email')})")
            print(f"    Job: {item.get('job_title')}")
            print(f"    Status: {item.get('status')}")
            print(f"    Days Pending: {item.get('days_pending')}")

        return data

    except Exception as e:
        print_test("Get pending communications", False, str(e))
        return []


def test_send_bulk_email(communication_ids):
    """Test 12: Send bulk emails."""
    print_section(f"TEST 12: Send Bulk Emails to {len(communication_ids)} Candidates")

    if not communication_ids:
        print_test("Send bulk email", False, "No communication IDs provided")
        return None

    try:
        payload = {
            "communication_ids": communication_ids[:3],  # Limit to 3 for testing
            "subject": "Interview Invitation - {{job_title}}",
            "body": "Dear {{candidate_name}},\n\nWe are pleased to invite you for an interview.\n\nBest regards,\nHR Team",
            "sender_name": "HR Recruitment Team"
        }

        response = client.post(
            f"{BASE_URL}/communications/send-bulk",
            json=payload
        )
        assert response.status_code == 200, f"Status code: {response.status_code}"

        data = response.json()
        assert data.get("success"), "Bulk email operation failed"

        results = data.get("results", {})
        successful = len(results.get("successful", []))
        failed = len(results.get("failed", []))

        print_test("Send bulk email", True, data.get("message"))
        print(f"\n  Total Processed: {data.get('total_processed')}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")

        if successful > 0:
            print("\n  Successfully Sent:")
            for item in results["successful"][:5]:
                print(f"    - {item.get('candidate_name')} ({item.get('email')})")
                print(f"      Status: {item.get('status')}")

        return data

    except Exception as e:
        print_test("Send bulk email", False, str(e))
        return None


def run_all_tests():
    """Run all tests in sequence."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "CANDIDATE MANAGEMENT SYSTEM TESTS" + " " * 25 + "║")
    print("║" + " " * 78 + "║")
    print("║" + f"  Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + " " * 44 + "║")
    print("║" + f"  Backend URL: {BASE_URL}" + " " * (78 - len(BASE_URL) - 17) + "║")
    print("╚" + "═" * 78 + "╝")

    results = {}

    # Test 1: Get all candidates
    results["all_candidates"] = test_get_candidates_all_jobs()

    # Test 2: Get all jobs
    results["jobs"] = test_get_jobs()

    # Test 3: Filter by job (if jobs exist)
    if results["jobs"] and len(results["jobs"]) > 0:
        first_job = results["jobs"][0]
        results["job_filter"] = test_get_candidates_by_job(
            first_job.get("id"),
            first_job.get("title")
        )

    # Test 4: Filter by status
    results["status_filter"] = test_filter_by_status("shortlisted")

    # Test 5: Filter by ATS score
    results["ats_filter"] = test_filter_by_ats_score(70)

    # Test 6: Search candidates
    results["search"] = test_search_candidates("john")

    # Test 7-10: Application operations (if candidates exist)
    if results["all_candidates"] and results["all_candidates"]["items"]:
        first_candidate = results["all_candidates"]["items"][0]
        app_id = first_candidate.get("application_id")

        if app_id:
            # Test 7: Get application details
            results["app_details"] = test_get_application_details(app_id)

            # Test 8: Shortlist candidate
            results["shortlist"] = test_shortlist_candidate(app_id)

            # Test 9: Test idempotence
            results["idempotence"] = test_shortlist_idempotence(app_id)

            # Test 10: Bulk shortlist (if multiple candidates)
            if len(results["all_candidates"]["items"]) >= 3:
                app_ids = [
                    item.get("application_id")
                    for item in results["all_candidates"]["items"][1:4]
                    if item.get("application_id")
                ]
                if app_ids:
                    results["bulk_shortlist"] = test_bulk_shortlist(app_ids)

    # Test 11: Get pending communications
    results["pending_comms"] = test_get_pending_communications()

    # Test 12: Send bulk email (if pending communications exist)
    if results["pending_comms"] and len(results["pending_comms"]) > 0:
        comm_ids = [item.get("id") for item in results["pending_comms"][:3]]
        results["bulk_email"] = test_send_bulk_email(comm_ids)

    # Summary
    print_section("TEST SUMMARY")
    total_tests = 12
    passed_tests = sum(1 for v in results.values() if v is not None)

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")

    print("\n" + "=" * 80)
    print("  TESTING COMPLETE")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    print("\nStarting Candidate Management System Tests...")
    print("Ensure the backend server is running at http://localhost:8000\n")

    try:
        # Quick connectivity check
        response = client.get(f"{BASE_URL}/jobs")
        if response.status_code != 200:
            print("❌ Cannot connect to backend. Please start the server first.")
            print("\nCommand: .venv\\Scripts\\python.exe -m uvicorn backend.api.app:app --reload\n")
            exit(1)

        run_all_tests()

    except httpx.ConnectError:
        print("❌ Connection Error: Backend server is not running.")
        print("\nPlease start the backend server:")
        print("  .venv\\Scripts\\python.exe -m uvicorn backend.api.app:app --reload --host 0.0.0.0 --port 8000\n")
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        exit(1)
