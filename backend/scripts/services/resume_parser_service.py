import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def extract_text_from_document(file_bytes: bytes, filename: str) -> str:
    """Extract raw text from a document based on its extension."""
    ext = filename.split(".")[-1].lower()
    
    if ext == "txt":
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1")
            
    elif ext == "pdf":
        return extract_text_pdfplumber(file_bytes) or extract_text_pymupdf(file_bytes)
        
    elif ext == "docx":
        return extract_text_docx(file_bytes)
        
    else:
        raise ValueError(f"Unsupported file extension: {ext}")


def extract_text_pdfplumber(file_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {e}")
        return ""


def extract_text_pymupdf(file_bytes: bytes) -> str:
    """Fallback PDF extraction using PyMuPDF."""
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()
    except Exception as e:
        logger.error(f"PyMuPDF extraction failed: {e}")
        raise ValueError("Failed to extract text from PDF")


def extract_text_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs]).strip()
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        raise ValueError("Failed to extract text from DOCX")
