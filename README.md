# AI Recruitment & Talent Management Copilot

A premium, modern single-page HR SaaS dashboard built with **Streamlit**, **Plotly**, and **Custom CSS**. This dashboard serves as a high-fidelity frontend mockup that can be easily connected to FastAPI backend systems and AI processing pipelines.

## ðŸ“ Project Directory Structure

```text
AI-Recruitment-Copilot/
â”‚
â”œâ”€â”€ app.py                      # Main application entry point
â”‚
â”œâ”€â”€ assets/
â”‚   â”œâ”€â”€ css/
â”‚   â”‚   â”œâ”€â”€ style.css           # Global layout & HTML body defaults
â”‚   â”‚   â”œâ”€â”€ cards.css           # Custom wrapper cards & KPI styles
â”‚   â”‚   â”œâ”€â”€ forms.css           # Button overrides & input selectors
â”‚   â”‚   â”œâ”€â”€ tables.css          # Candidate table row layouts & timeline
â”‚   â”‚   â””â”€â”€ animations.css      # Fade-in keyframes & hover states
â”‚   â”‚
â”‚   â”œâ”€â”€ images/                 # UI assets (logo, banner, avatars)
â”‚   â”‚   â”œâ”€â”€ logo.png
â”‚   â”‚   â”œâ”€â”€ profile.png
â”‚   â”‚   â””â”€â”€ banner.png
â”‚   â”‚
â”‚   â””â”€â”€ icons/
â”‚
â”œâ”€â”€ components/
â”‚   â”œâ”€â”€ header.py               # Section 1: Dynamic dashboard header
â”‚   â”œâ”€â”€ workflow.py             # Candidate recruitment status pipeline
â”‚   â”œâ”€â”€ dashboard_cards.py      # Section 2: Overviews & KPI counters
â”‚   â”œâ”€â”€ create_job.py           # Section 3: Job requirements configuration
â”‚   â”œâ”€â”€ upload_resume.py        # Section 4: Drag & Drop resume uploader
â”‚   â”œâ”€â”€ resume_analysis.py      # Section 5: Candidate parsed details
â”‚   â”œâ”€â”€ job_match.py            # Section 6: Required vs Candidate skills comparison
â”‚   â”œâ”€â”€ candidate_table.py      # Section 7: Searchable database screening board
â”‚   â”œâ”€â”€ analytics.py            # Section 8: Five Plotly insight charts
â”‚   â”œâ”€â”€ recommendation.py       # Section 9: Fit assessments (strengths & dev areas)
â”‚   â”œâ”€â”€ timeline.py             # Section 10: Chronological activities timeline
â”‚   â””â”€â”€ footer.py               # Section 11: Credits & version details
â”‚
â”œâ”€â”€ utils/
â”‚   â”œâ”€â”€ styles.py               # Modular CSS loader & injector utility
â”‚   â””â”€â”€ dummy_data.py           # Database initial states seeder
â”‚
â”œâ”€â”€ requirements.txt            # Required packages lists
â”‚
â””â”€â”€ README.md                   # This instruction guide
```

---

## ðŸš€ Getting Started

### 1. Set Up Environment
Create a virtual environment and activate it:
```bash
python -m venv venv
# On Windows powershell:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
Install all required libraries using pip:
```bash
pip install -r requirements.txt
```

### 3. Launch Application
Navigate to the directory and run the Streamlit app:
```bash
streamlit run app.py
```
The app will automatically compile and open a browser window displaying the recruitment board dashboard interface.

### Email notifications

Recruiter decisions (`Shortlisted`, `Approved`, and `Rejected`) can notify candidates by email. Configure SMTP before starting the backend:

```powershell
$env:SMTP_HOST = "smtp.example.com"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "your-username"
$env:SMTP_PASSWORD = "your-password"
$env:SMTP_FROM_EMAIL = "recruiting@example.com"
$env:SMTP_USE_TLS = "true"
```

The candidate's email address is used as the recipient. A successful notification is recorded per decision, so repeating the same decision does not send another message.

