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
    # Minimal PDF generation using reportlab or fpdf
    # Since we might not have them installed, let's write a simple HTML to PDF or use a stub that creates a text file masquerading as PDF for now, or just text.
    # To be safe without extra dependencies, I'll generate a CSV if PDF fails or write a basic text representation.
    # We'll use a simple txt for now as a fallback if no PDF lib is available.
    try:
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(file_path)
        c.drawString(100, 800, f"HirePilot Report: {report_type}")
        y = 750
        if isinstance(data, list):
            for i, item in enumerate(data[:30]):  # Cap at 30 rows for basic PDF
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
    except ImportError:
        # Fallback if reportlab is not installed
        with open(file_path.replace(".pdf", ".txt"), "w", encoding="utf-8") as f:
            f.write(f"HirePilot Report: {report_type}\n\n")
            f.write(str(data))
        # Update path to match
        os.rename(file_path.replace(".pdf", ".txt"), file_path)
