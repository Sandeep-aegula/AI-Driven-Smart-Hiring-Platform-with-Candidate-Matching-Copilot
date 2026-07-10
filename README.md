# AI Recruitment & Talent Management Copilot

A premium, modern single-page HR SaaS dashboard built with **Streamlit**, **Plotly**, and **Custom CSS**. This dashboard serves as a high-fidelity frontend mockup that can be easily connected to FastAPI backend systems and AI processing pipelines.

## 📁 Project Directory Structure

```text
AI-Recruitment-Copilot/
│
├── app.py                      # Main application entry point
│
├── assets/
│   ├── css/
│   │   ├── style.css           # Global layout & HTML body defaults
│   │   ├── cards.css           # Custom wrapper cards & KPI styles
│   │   ├── forms.css           # Button overrides & input selectors
│   │   ├── tables.css          # Candidate table row layouts & timeline
│   │   └── animations.css      # Fade-in keyframes & hover states
│   │
│   ├── images/                 # UI assets (logo, banner, avatars)
│   │   ├── logo.png
│   │   ├── profile.png
│   │   └── banner.png
│   │
│   └── icons/
│
├── components/
│   ├── header.py               # Section 1: Dynamic dashboard header
│   ├── workflow.py             # Candidate recruitment status pipeline
│   ├── dashboard_cards.py      # Section 2: Overviews & KPI counters
│   ├── create_job.py           # Section 3: Job requirements configuration
│   ├── upload_resume.py        # Section 4: Drag & Drop resume uploader
│   ├── resume_analysis.py      # Section 5: Candidate parsed details
│   ├── job_match.py            # Section 6: Required vs Candidate skills comparison
│   ├── candidate_table.py      # Section 7: Searchable database screening board
│   ├── analytics.py            # Section 8: Five Plotly insight charts
│   ├── recommendation.py       # Section 9: Fit assessments (strengths & dev areas)
│   ├── timeline.py             # Section 10: Chronological activities timeline
│   └── footer.py               # Section 11: Credits & version details
│
├── utils/
│   ├── styles.py               # Modular CSS loader & injector utility
│   └── dummy_data.py           # Database initial states seeder
│
├── requirements.txt            # Required packages lists
│
└── README.md                   # This instruction guide
```

---

## 🚀 Getting Started

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
