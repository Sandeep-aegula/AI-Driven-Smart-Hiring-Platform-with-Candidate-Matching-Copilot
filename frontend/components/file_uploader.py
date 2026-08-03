"""
Global File Uploader Component for HirePilot.

Simple, compact file upload component that mirrors Streamlit's native
look — a visible label, a slim gray bar with an "Upload" button and a
size/type caption. No custom dropzone box.
"""

import streamlit as st
from typing import List, Optional, Callable, Any
import uuid


def file_uploader(
    label: str = "Upload file",
    accepted_types: Optional[List[str]] = None,
    max_size_mb: int = 200,
    key: Optional[str] = None,
    on_change: Optional[Callable] = None,
    disabled: bool = False,
    multiple: bool = False,
) -> Any:
    if key is None:
        key = f"file_uploader_{uuid.uuid4().hex[:8]}"

    _inject_uploader_css()

    uploaded_file = st.file_uploader(
        label=label,
        type=accepted_types,
        accept_multiple_files=multiple,
        key=f"{key}_native",
        on_change=on_change,
        disabled=disabled,
        label_visibility="visible",  # keep the label shown, e.g. "Upload Resume *"
    )
    return uploaded_file


def _inject_uploader_css():
    css = """
    <style>
    /* Compact single-row bar instead of the big dashed dropzone */
    div[data-testid="stFileUploaderDropzone"],
    section[data-testid="stFileUploadDropzone"] {
        border: none !important;
        background-color: #F1F5F9 !important;
        border-radius: 10px !important;
        padding: 8px 14px !important;
        min-height: unset !important;
    }

    /* Small white "Upload" button */
    div[data-testid="stFileUploaderDropzone"] button,
    section[data-testid="stFileUploadDropzone"] button,
    [data-testid="stBaseButton-secondary"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        padding: 6px 14px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        box-shadow: none !important;
    }

    div[data-testid="stFileUploaderDropzone"] button:hover,
    section[data-testid="stFileUploadDropzone"] button:hover {
        border-color: #6366F1 !important;
        color: #6366F1 !important;
    }

    /* Caption text (size/type) sits inline, muted */
    div[data-testid="stFileUploaderDropzoneInstructions"] {
        color: #64748B !important;
        font-size: 0.85rem !important;
    }

    /* Field label above the uploader */
    div[data-testid="stFileUploader"] > label {
        font-weight: 500 !important;
        color: #0F172A !important;
        font-size: 0.9rem !important;
        margin-bottom: 4px !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def file_uploader_simple(
    label: str = "Upload Resume",
    accepted_types: Optional[List[str]] = None,
    max_size_mb: int = 200,
    key: Optional[str] = None,
    on_change: Optional[Callable] = None,
    disabled: bool = False,
    multiple: bool = False,
) -> Any:
    return file_uploader(
        label=label,
        accepted_types=accepted_types,
        max_size_mb=max_size_mb,
        key=key,
        on_change=on_change,
        disabled=disabled,
        multiple=multiple,
    )