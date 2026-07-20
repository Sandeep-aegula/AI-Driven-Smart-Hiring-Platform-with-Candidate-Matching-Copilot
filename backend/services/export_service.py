import os
import uuid
import pandas as pd
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

# In-memory status store for simplicity
# Structure: { "export_id": {"status": "processing"|"completed"|"failed", "file_path": str, "error": str} }
_export_tasks = {}

def get_export_status(export_id: str) -> dict:
    return _export_tasks.get(export_id, {"status": "not_found"})

async def generate_export(report_type: str, format: str, data: list[dict] | dict) -> str:
    """
    Kicks off an async background export task and returns the export_id.
    """
    export_id = str(uuid.uuid4())
    _export_tasks[export_id] = {"status": "processing", "file_path": None, "error": None}
    
    # Run the CPU-bound export generation in a thread
    asyncio.create_task(_run_export_task(export_id, report_type, format, data))
    return export_id

async def _run_export_task(export_id: str, report_type: str, format: str, data: list[dict] | dict):
    try:
        # Give event loop a breather
        await asyncio.sleep(0.1)
        
        file_name = f"{report_type}_{datetime.utcnow().strftime('%Y%md_%H%M%S')}_{export_id[:8]}"
        file_path = ""
        
        if format == "csv":
            file_path = os.path.join(EXPORT_DIR, f"{file_name}.csv")
            _generate_csv(data, file_path)
        elif format == "xlsx":
            file_path = os.path.join(EXPORT_DIR, f"{file_name}.xlsx")
            _generate_excel(data, file_path)
        elif format == "pdf":
            file_path = os.path.join(EXPORT_DIR, f"{file_name}.pdf")
            _generate_pdf(data, file_path, report_type)
        else:
            raise ValueError("Unsupported format")
            
        _export_tasks[export_id]["status"] = "completed"
        _export_tasks[export_id]["file_path"] = file_path
        
    except Exception as e:
        logger.error(f"Export {export_id} failed: {e}")
        _export_tasks[export_id]["status"] = "failed"
        _export_tasks[export_id]["error"] = str(e)

def _generate_csv(data, file_path):
    if isinstance(data, dict):
        # Convert dict to single row or appropriate format
        data = [data]
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)

def _generate_excel(data, file_path):
    if isinstance(data, dict):
        data = [data]
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False, engine='openpyxl')

def _generate_pdf(data, file_path, report_type):
    try:
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            ListFlowable,
            ListItem,
            PageBreak,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch

        if report_type.startswith("job_report") and isinstance(data, dict):
            story = _build_job_report_story(data)
            doc = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )
            doc.build(story)
        else:
            _generate_simple_pdf(data, file_path, report_type)
    except ImportError:
        with open(file_path.replace(".pdf", ".txt"), "w", encoding="utf-8") as f:
            f.write(f"HirePilot Report: {report_type}\n\n")
            f.write(str(data))
        os.rename(file_path.replace(".pdf", ".txt"), file_path)


def _format_date(value):
    if not value:
        return "N/A"
    try:
        from datetime import datetime

        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d %B %Y")
    except Exception:
        return str(value)


def _build_hiring_summary(job):
    parts = []
    if job.get("title"):
        parts.append(f"actively hiring for a {job['title']}")
    if job.get("department"):
        parts.append(f"within the {job['department']} department")
    required = job.get("required_skills") or job.get("requirements") or []
    if required:
        parts.append(f"The role requires strong {', '.join(str(s) for s in required[:3])} skills")
    if job.get("experience_min") or job.get("experience_max"):
        parts.append(f"with {job.get('experience_min')}–{job.get('experience_max')} years of experience")
    if job.get("deadline"):
        parts.append(f"Applications remain open until {_format_date(job.get('deadline'))}")
    return "This position is " + " ".join(parts) + "." if parts else None


def _build_job_report_story(data: dict):
    from reportlab.platypus import (
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        ListFlowable,
        ListItem,
    )
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import inch

    styles = getSampleStyleSheet()
    story = []
    job = data.get("job") or {}
    pipeline = data.get("pipeline") or {}
    candidates = data.get("candidates") or []

    story.append(Paragraph("HirePilot Job Report", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Basic Information", styles["Heading2"]))
    basic_info = [
        ["Job Title", job.get("title") or "N/A"],
        ["Department", job.get("department") or "N/A"],
        ["Employment Type", job.get("employment_type") or "N/A"],
        ["Location", job.get("location") or "N/A"],
        ["Status", job.get("status") or "N/A"],
        ["Hiring Manager", job.get("hiring_manager") or "N/A"],
        ["Application Deadline", _format_date(job.get("deadline"))],
        [
            "Salary Range",
            f"₹{job.get('salary_min')}–{job.get('salary_max')} LPA"
            if job.get("salary_min") or job.get("salary_max")
            else "N/A",
        ],
        [
            "Experience Required",
            f"{job.get('experience_min')}–{job.get('experience_max')} Years"
            if job.get("experience_min") or job.get("experience_max")
            else "N/A",
        ],
    ]
    basic_table = Table(basic_info, colWidths=[2.2 * inch, 4.3 * inch])
    basic_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2FF")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(basic_table)
    story.append(Spacer(1, 0.2 * inch))

    description = job.get("description")
    if description:
        story.append(Paragraph("Job Description", styles["Heading2"]))
        story.append(Paragraph(str(description), styles["BodyText"]))
        story.append(Spacer(1, 0.15 * inch))

    responsibilities = job.get("responsibilities") or []
    if responsibilities:
        story.append(Paragraph("Key Responsibilities", styles["Heading2"]))
        story.append(
            ListFlowable(
                [ListItem(Paragraph(str(r), styles["BodyText"])) for r in responsibilities],
                bulletType="bullet",
                leftIndent=20,
            )
        )
        story.append(Spacer(1, 0.15 * inch))

    required_skills = job.get("required_skills") or job.get("requirements") or []
    if required_skills:
        story.append(Paragraph("Required Skills", styles["Heading2"]))
        story.append(Paragraph(", ".join(str(s) for s in required_skills), styles["BodyText"]))
        story.append(Spacer(1, 0.15 * inch))

    preferred_skills = job.get("preferred_skills") or job.get("nice_to_have_skills") or []
    if preferred_skills:
        story.append(Paragraph("Preferred Skills", styles["Heading2"]))
        story.append(Paragraph(", ".join(str(s) for s in preferred_skills), styles["BodyText"]))
        story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Pipeline Summary", styles["Heading2"]))
    pipeline_data = [
        ["Total Candidates", str(pipeline.get("total_candidates", 0))],
        ["Qualified Candidates", str(pipeline.get("qualified", 0))],
        ["Interviews Scheduled", str(pipeline.get("interviews", 0))],
        ["Offers Released", str(pipeline.get("offers_released", 0))],
        ["Hired", str(pipeline.get("hired", 0))],
    ]
    pipeline_table = Table(pipeline_data, colWidths=[2.5 * inch, 2.5 * inch])
    pipeline_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2FF")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(pipeline_table)
    story.append(Spacer(1, 0.2 * inch))

    if candidates:
        story.append(Paragraph("Candidate Summary", styles["Heading2"]))
        candidate_data = [["Name", "Match Score", "Status", "Email"]]
        for c in candidates[:20]:
            candidate_data.append(
                [
                    c.get("name") or "Unknown",
                    str(c.get("match_score", "N/A")),
                    c.get("status") or "Unknown",
                    c.get("email") or "",
                ]
            )
        candidate_table = Table(
            candidate_data, colWidths=[1.8 * inch, 1.2 * inch, 1.5 * inch, 2 * inch]
        )
        candidate_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366F1")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9FAFB")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(candidate_table)
        story.append(Spacer(1, 0.2 * inch))

    summary = _build_hiring_summary(job)
    if summary:
        story.append(Paragraph("Hiring Summary", styles["Heading2"]))
        story.append(Paragraph(summary, styles["BodyText"]))

    return story


def _generate_simple_pdf(data, file_path, report_type):
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(file_path)
    c.drawString(100, 800, f"HirePilot Report: {report_type}")
    y = 750
    if isinstance(data, list):
        for i, item in enumerate(data[:30]):
            c.drawString(50, y, str(item)[:100])
            y -= 20
            if y < 50:
                c.showPage()
                y = 800
    else:
        for k, v in data.items():
            c.drawString(50, y, f"{k}: {str(v)[:80]}")
            y -= 20
    c.save()
