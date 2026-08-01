# Candidate Management System - Implementation Guide

## Overview

This document describes the complete implementation of the Candidate Management system for HirePilot - AI Recruitment & Talent Management Copilot.

## Architecture

### Database Layer
- **Model**: `Communication` (backend/models/entities.py)
- **Database**: MySQL with async SQLAlchemy
- **Connection**: mysql+aiomysql://

### Backend Layer
- **Framework**: FastAPI with async/await
- **Routes**: 
  - `/candidates` - Candidate management
  - `/communications` - Communication queue
- **Session Management**: AsyncSessionLocal with get_db_session

### Frontend Layer
- **Framework**: Streamlit
- **Page**: frontend/views/candidate_management.py
- **Component**: frontend/components/communications.py

---

## Database Models

### Communication Model

```python
class Communication(Base):
    __tablename__ = "communications"
    
    id: int
    candidate_id: int (FK -> candidates.id)
    application_id: int (FK -> applications.id)
    job_id: int (FK -> jobs.id)
    recruitment_round: str
    status: str (pending, sent, failed, read)
    email: str
    subject: str
    message: str
    email_template: str
    queued_at: datetime
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime
```

**Indexes**:
- candidate_id
- application_id
- job_id
- status
- email

**Foreign Keys**:
- candidate_id -> candidates(id) ON DELETE CASCADE
- application_id -> applications(id) ON DELETE CASCADE
- job_id -> jobs(id) ON DELETE CASCADE

---

## API Endpoints

### 1. GET /candidates

**Query Parameters**:
```
- search: str (search by name, email)
- status: str (filter by application status)
- skill: str (reserved for future use)
- job_id: int (filter by job ID)
- min_match_score: int (minimum ATS score)
- limit: int (default 100)
- offset: int (default 0)
- sort_by: str (ats_score, name, applied_at)
- sort_order: str (asc, desc)
```

**Response**:
```json
{
  "items": [
    {
      "id": 1,
      "application_id": 5,
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "current_title": "Software Engineer",
      "years_experience": 5,
      "location": "New York",
      "status": "shortlisted",
      "ats_score": 85,
      "match_score": 80,
      "created_at": "2026-07-15T10:30:00",
      "updated_at": "2026-07-20T14:20:00"
    }
  ],
  "total": 12,
  "limit": 100,
  "offset": 0,
  "status_counts": {
    "submitted": 3,
    "under_review": 4,
    "shortlisted": 5
  },
  "average_ats_score": 76.5,
  "selected_job_title": "Frontend Developer",
  "role_candidate_count": 12
}
```

### 2. POST /candidates/applications/{application_id}/shortlist

**Request**: No body required

**Response**:
```json
{
  "success": true,
  "message": "Candidate shortlisted successfully",
  "application_id": 5,
  "candidate_id": 1,
  "candidate_name": "John Doe",
  "job_title": "Frontend Developer",
  "status": "shortlisted",
  "communication_created": true
}
```

### 3. POST /candidates/applications/shortlist-bulk

**Request Body**:
```json
[12, 15, 18]
```

**Response**:
```json
{
  "success": true,
  "message": "Shortlisted 3 candidates (0 already shortlisted, 0 failed)",
  "results": {
    "successful": [
      {
        "application_id": 12,
        "candidate_id": 1,
        "candidate_name": "John Doe",
        "job_title": "Frontend Developer"
      }
    ],
    "failed": [],
    "already_shortlisted": []
  },
  "total_processed": 3,
  "total_successful": 3,
  "total_already_shortlisted": 0,
  "total_failed": 0
}
```

### 4. GET /candidates/applications/{application_id}

**Response**:
```json
{
  "id": 5,
  "candidate_id": 1,
  "job_id": 2,
  "status": "shortlisted",
  "match_score": 80,
  "candidate": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "years_experience": 5,
    "location": "New York"
  },
  "job": {
    "id": 2,
    "title": "Frontend Developer",
    "department": "Engineering"
  },
  "resume": {
    "id": 3,
    "original_filename": "john_doe_resume.pdf",
    "storage_path": "/uploads/resumes/...",
    "mime_type": "application/pdf",
    "file_size": 245678,
    "uploaded_at": "2026-07-15T10:30:00"
  },
  "ats_score": {
    "id": 7,
    "ats_score": 85,
    "skills_score": 90,
    "experience_score": 85,
    "education_score": 80,
    "keyword_score": 85,
    "recommendation": "strong_match",
    "strengths": ["React expertise", "5+ years experience"],
    "gaps": ["TypeScript certification"],
    "scored_at": "2026-07-15T11:00:00"
  }
}
```

### 5. GET /communications/pending

**Response**:
```json
[
  {
    "id": 1,
    "candidate_id": 1,
    "application_id": 5,
    "job_id": 2,
    "candidate_name": "John Doe",
    "candidate_email": "john@example.com",
    "job_title": "Frontend Developer",
    "department": "Engineering",
    "round": "Initial Screening",
    "status": "pending",
    "subject": "Application Update: Frontend Developer",
    "message": "Dear John Doe...",
    "queued_at": "2026-07-20T14:20:00",
    "days_pending": 2
  }
]
```

### 6. POST /communications/send-bulk

**Request Body**:
```json
{
  "communication_ids": [1, 2, 3],
  "subject": "Interview Invitation - {{job_title}}",
  "body": "Dear {{candidate_name}},\n\nWe are pleased to invite you...",
  "sender_name": "HR Recruitment Team"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Sent 3 emails, 0 failed",
  "total_processed": 3,
  "total_successful": 3,
  "total_failed": 0,
  "results": {
    "successful": [
      {
        "communication_id": 1,
        "candidate_id": 1,
        "candidate_name": "John Doe",
        "email": "john@example.com",
        "status": "sent"
      }
    ],
    "failed": []
  }
}
```

---

## Frontend Implementation

### Candidate Management Page

**Location**: `frontend/views/candidate_management.py`

**Key Features**:

1. **Header Section**
   - Title: "Candidate Management"
   - Subtitle: "Review, compare, and shortlist candidates using AI"
   - Refresh button

2. **Filters**
   - Job Role dropdown (All Jobs + dynamic job list)
   - Status dropdown (All, submitted, under_review, shortlisted, interview, rejected)
   - Minimum ATS Score slider (0-100, step 5)
   - Search field (name, email, skills)
   - Clear Filters button

3. **Summary Cards**
   - Total Candidates (dynamic based on job filter)
   - Average ATS Score (calculated from filtered candidates)
   - Shortlisted Count
   - Under Review Count

4. **Status Breakdown**
   - Expandable section showing count by status
   - Updates when job role changes

5. **Bulk Actions Bar**
   - Shows when candidates are selected
   - "Shortlist Selected (N)" button
   - "Clear Selection" button

6. **Candidate Table**
   - Columns: Checkbox, ID, Name/Email, ATS Score, Status, Experience, Applied Date, Actions
   - Color-coded ATS scores (Green ≥75%, Yellow ≥50%, Red <50%)
   - Status badges
   - Action buttons: Resume, Select, Shortlist, View

7. **Resume Panel (Sidebar)**
   - Candidate information
   - ATS Score display with color coding
   - Score breakdown (Skills, Experience, Education, Keywords)
   - Strengths and Gaps
   - Resume file information
   - Download button (placeholder)
   - Shortlist button

### Communications Component

**Location**: `frontend/components/communications.py`

**Key Features**:

1. **Pending Queue**
   - List of shortlisted candidates awaiting communication
   - Checkbox for bulk selection
   - "Select All" / "Clear Selection" buttons
   - Shows: Name, Email, Job, Department, Round, Days Pending

2. **Bulk Email Form**
   - Subject field
   - Sender Name field
   - Body textarea with placeholder support
   - Placeholders: `{{candidate_name}}`, `{{job_title}}`
   - "Send to N Candidates" button
   - Clear button

3. **Communication History**
   - Shows sent/failed communications
   - Pagination support

---

## Database Migration

### Migration Script

**File**: `backend/database/add_communication_table.py`

**Status**: ✅ Already executed (table exists)

**What it does**:
- Creates `communications` table
- Adds indexes and foreign keys
- Checks if table already exists before creation

**To run manually** (if needed):
```bash
.venv/Scripts/python.exe -m backend.database.add_communication_table
```

---

## Testing Checklist

### 1. Job Role Filtering
- [ ] Select "All Jobs" - verify all candidates appear
- [ ] Select "Frontend Developer" - verify only Frontend Developer applicants
- [ ] Verify candidate count updates
- [ ] Verify status counts update
- [ ] Verify average ATS score updates

### 2. Status Filtering
- [ ] Filter by "submitted" - verify only submitted applications
- [ ] Filter by "shortlisted" - verify only shortlisted
- [ ] Combine with job role filter

### 3. ATS Score Filtering
- [ ] Set minimum score to 70% - verify candidates with <70% are hidden
- [ ] Set to 0% - verify all candidates appear

### 4. Search Functionality
- [ ] Search by candidate name
- [ ] Search by email
- [ ] Verify search works with other filters

### 5. Candidate Table
- [ ] Verify all columns display correctly
- [ ] Verify ATS scores are color-coded
- [ ] Verify status badges appear
- [ ] Verify dates are formatted correctly

### 6. Selection and Bulk Actions
- [ ] Select individual candidates
- [ ] Verify selection persists
- [ ] Select multiple candidates
- [ ] Verify bulk actions bar appears
- [ ] Clear selection

### 7. Shortlist Functionality
- [ ] Shortlist single candidate
- [ ] Verify application status updates to "shortlisted"
- [ ] Verify communication record created
- [ ] Verify idempotence (shortlist again - no duplicate)
- [ ] Bulk shortlist multiple candidates
- [ ] Verify all selected candidates are shortlisted

### 8. Resume Panel
- [ ] Click "View" button
- [ ] Verify candidate information displays
- [ ] Verify ATS score displays with color
- [ ] Verify score breakdown shows
- [ ] Verify resume filename uses `original_filename`
- [ ] Close panel

### 9. Communications Integration
- [ ] Shortlist a candidate
- [ ] Navigate to Communications tab
- [ ] Verify candidate appears in Pending Queue
- [ ] Verify all details are correct
- [ ] Select multiple pending candidates
- [ ] Send bulk email
- [ ] Verify status changes to "sent"
- [ ] Verify sent_at timestamp recorded

### 10. Data Persistence
- [ ] Refresh browser
- [ ] Verify shortlisted status persists
- [ ] Verify communication records persist
- [ ] Restart backend
- [ ] Verify all data still accessible

### 11. Error Handling
- [ ] Try to shortlist with invalid application ID
- [ ] Verify proper error message
- [ ] Test with no candidates
- [ ] Test with no ATS scores
- [ ] Verify graceful handling

### 12. Integration with Existing Features
- [ ] Verify job applications still work
- [ ] Verify resume uploads still work
- [ ] Verify resume parsing still works
- [ ] Verify ATS scoring still works
- [ ] Verify analytics dashboard still works
- [ ] Verify interviews module still works
- [ ] Verify onboarding module still works
- [ ] Verify employees module still works
- [ ] Verify AI Copilot still works

---

## Commands to Run

### 1. Database Migration (if needed)
```bash
.venv/Scripts/python.exe -m backend.database.add_communication_table
```

### 2. Start Backend
```bash
.venv/Scripts/python.exe -m uvicorn backend.api.app:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start Frontend
```bash
.venv/Scripts/streamlit.exe run frontend/app.py
```

### 4. Access Application
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Candidate Management Flow                 │
└─────────────────────────────────────────────────────────────┘

1. Candidate Application
   ↓
2. Resume Upload & Parsing
   ↓
3. ATS Scoring (ApplicationScore)
   ↓
4. Candidate Review (Candidate Management Page)
   ├─ Filter by Job Role
   ├─ Filter by Status
   ├─ Filter by ATS Score
   ├─ Search by Name/Email
   └─ View Resume Details
   ↓
5. Shortlist Candidate
   ├─ Update Application.status = "shortlisted"
   └─ Create Communication record (status = "pending")
   ↓
6. Communications Tab
   ├─ View Pending Queue
   ├─ Select Candidates
   ├─ Compose Email (with placeholders)
   └─ Send Bulk Email
   ↓
7. Communication Record Updated
   ├─ status = "sent"
   ├─ sent_at = NOW()
   └─ subject, message stored
   ↓
8. Communication History
```

---

## Key Implementation Details

### 1. Job-Specific Filtering

The system correctly filters candidates based on the selected job:

```python
# Backend logic
if job_id:
    # Get candidate IDs who applied for this job
    app_stmt = select(Application.candidate_id).where(Application.job_id == job_id)
    candidate_ids = [row[0] for row in result]
    
    # Filter candidates by these IDs
    stmt = select(Candidate).where(Candidate.id.in_(candidate_ids))
```

### 2. ATS Score Calculation

ATS scores are application-specific and stored in `ApplicationScore`:

```python
# Get ATS score for specific job
for app in candidate.applications:
    if app.job_id == job_id:
        for score in app.scores:
            ats_score = score.ats_score
```

### 3. Transaction Safety

Shortlist operations use database transactions:

```python
async with get_db_session() as session:
    # Update application
    application.status = "shortlisted"
    
    # Create communication record
    communication = Communication(...)
    session.add(communication)
    
    # Commit both or rollback
    await session.commit()
```

### 4. Idempotence

Shortlist operations are idempotent:

```python
# Check if already shortlisted
if application.status == "shortlisted":
    return {"success": True, "message": "Already shortlisted"}

# Check if communication already exists
existing_comm = await session.execute(
    select(Communication).where(
        Communication.application_id == app_id,
        Communication.status == "pending"
    )
)
if not existing_comm.scalar_one_or_none():
    # Create new communication record
```

### 5. Bulk Operations

Bulk shortlist processes each candidate individually:

```python
for app_id in application_ids:
    try:
        # Process application
        # Create communication
        results["successful"].append(...)
    except Exception as e:
        results["failed"].append(...)

await session.commit()
```

---

## Troubleshooting

### Issue: Communications table doesn't exist

**Solution**:
```bash
.venv/Scripts/python.exe -m backend.database.add_communication_table
```

### Issue: No candidates appear

**Check**:
1. Verify backend is running
2. Check database connection
3. Verify candidates exist in database
4. Check browser console for errors

### Issue: ATS scores show as 0

**Check**:
1. Verify ApplicationScore records exist
2. Check if scoring service ran
3. Verify job_id matches application

### Issue: Shortlist doesn't work

**Check**:
1. Verify application_id is correct
2. Check backend logs for errors
3. Verify Communications table exists
4. Check foreign key constraints

---

## Performance Considerations

### 1. Pagination

The system uses backend pagination:
- Limit: 100 candidates per page (configurable)
- Offset: Calculated based on page number
- Total count: Cached for performance

### 2. Eager Loading

Related data is loaded efficiently:
```python
stmt = select(Application).options(
    selectinload(Application.candidate),
    selectinload(Application.job),
    selectinload(Application.scores)
)
```

### 3. Indexes

Key indexes:
- `communications.candidate_id`
- `communications.application_id`
- `communications.job_id`
- `communications.status`
- `communications.email`

### 4. Caching

Frontend uses session state for:
- Selected filters
- Selected candidates
- Current page

---

## Security Considerations

### 1. SQL Injection Prevention

All queries use SQLAlchemy ORM with parameterized queries.

### 2. Input Validation

- Application IDs validated before processing
- Email addresses validated
- File uploads (future) will be validated

### 3. Transaction Integrity

All multi-step operations use database transactions.

### 4. Error Messages

User-facing errors don't expose internal details.

---

## Future Enhancements

1. **Resume Download**
   - Implement actual file download
   - Support PDF preview

2. **Advanced Filters**
   - Skills-based filtering
   - Experience range
   - Location-based filtering

3. **Export Functionality**
   - Export candidates to CSV/Excel
   - Include ATS scores and match details

4. **Email Templates**
   - Pre-defined templates
   - Template variables
   - Rich text editor

5. **Notification System**
   - Email notifications to HR
   - Candidate status updates
   - Webhook integrations

---

## Maintenance

### Regular Tasks

1. **Database Cleanup**
   - Archive old communication records
   - Clean up failed communications

2. **Performance Monitoring**
   - Monitor query performance
   - Optimize slow queries
   - Review index usage

3. **Backup Strategy**
   - Regular database backups
   - Test restoration process

---

## Support

For issues or questions:
1. Check this documentation
2. Review backend logs
3. Check browser console
4. Verify database connectivity

---

**Last Updated**: 2026-08-01
**Version**: 1.0
**Status**: Production Ready
