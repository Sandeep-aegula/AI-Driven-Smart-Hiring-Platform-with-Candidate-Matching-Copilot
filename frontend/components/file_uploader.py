"""
Global File Uploader Component for HirePilot.

A clean, reusable file upload component that wraps Streamlit's native file_uploader
with custom styling via CSS injection.
"""

import streamlit as st
from typing import List, Optional, Callable, Any
import uuid


def file_uploader(
    label: str = "Upload file",
    help_text: str = "Limit 200MB per file • PDF, DOCX, TXT",
    accepted_types: Optional[List[str]] = None,
    max_size_mb: int = 200,
    key: Optional[str] = None,
    on_change: Optional[Callable] = None,
    disabled: bool = False,
    multiple: bool = False,
) -> Any:
    """
    Render a clean file uploader component using Streamlit's native file_uploader
    with custom styling via CSS injection.
    
    Args:
        label: Accessible label for the file uploader (required for accessibility)
        help_text: Help text with size limit and allowed types
        accepted_types: List of accepted file extensions (e.g., ["pdf", "docx", "txt"])
        max_size_mb: Maximum file size in MB
        key: Unique key for the component
        on_change: Callback when file is selected
        disabled: Whether the uploader is disabled
        multiple: Whether to accept multiple files
    
    Returns:
        Uploaded file(s) or None
    """
    # Generate a unique key if not provided
    if key is None:
        key = f"file_uploader_{uuid.uuid4().hex[:8]}"
    
    # Build dynamic help text if not provided
    if help_text == "Limit 200MB per file • PDF, DOCX, TXT" and accepted_types:
        types_str = ", ".join([t.upper() for t in accepted_types])
        help_text = f"Limit {max_size_mb}MB per file • {types_str}"
    
    # Inject custom CSS for this specific uploader instance
    _inject_uploader_css(key, max_size_mb, accepted_types)
    
    # Container with custom CSS class for styling
    with st.container():
        st.markdown(
            f'<div class="hirepilot-file-uploader-wrapper" data-key="{key}" data-max-size="{max_size_mb}">',
            unsafe_allow_html=True
        )
        
        # Native file uploader with proper label for accessibility
        uploaded_file = st.file_uploader(
            label=label,  # Non-empty label for accessibility
            type=accepted_types,
            accept_multiple_files=multiple,
            key=f"{key}_native",
            on_change=on_change,
            disabled=disabled,
            label_visibility="collapsed",  # Hide label visually but keep for accessibility
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return uploaded_file


def _inject_uploader_css(key: str, max_size_mb: int, accepted_types: Optional[List[str]]):
    """Inject custom CSS for the file uploader to style the native Streamlit uploader."""
    if accepted_types:
        types_str = ", ".join([t.upper() for t in accepted_types])
    else:
        types_str = "PDF, DOCX, TXT"
    
    css = f"""
    <style>
    /* Hide the default Streamlit file uploader label since we use label_visibility="collapsed" */
    div[data-testid="stFileUploader"] > label {{
        display: none !important;
    }}
    
    /* Style the file uploader dropzone */
    div[data-testid="stFileUploader"] {{
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
    }}
    
    div[data-testid="stFileUploader"] > div:first-child {{
        display: none !important;
    }}
    
    div[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] {{
        border: 2px dashed #CBD5E1 !important;
        background-color: #F8FAFC !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        transition: all 0.2s ease !important;
        min-height: 72px !important;
        display: flex !important;
        align-items: center !important;
        gap: 16px !important;
    }}
    
    div[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"]:hover {{
        border-color: #6366F1 !important;
        background-color: #EEF2FF !important;
    }}
    
    /* Style the dropzone instructions text */
    div[data-testid="stFileUploadDropzoneInstructions"] {{
        display: flex !important;
        align-items: center !important;
        gap: 16px !important;
        width: 100% !important;
        flex: 1 !important;
    }}
    
    /* Style the "Drag and drop file here" text */
    div[data-testid="stFileUploadDropzoneInstructions"] > div:first-child {{
        display: flex !important;
        flex-direction: column !important;
        gap: 4px !important;
        flex: 1 !important;
    }}
    
    div[data-testid="stFileUploadDropzoneInstructions"] > div:first-child > div:first-child {{
        font-size: 0.9375rem !important;
        font-weight: 500 !important;
        color: #0F172A !important;
        line-height: 1.4 !important;
    }}
    
    div[data-testid="stFileUploadDropzoneInstructions"] > div:first-child > div:last-child {{
        font-size: 0.75rem !important;
        font-weight: 400 !important;
        color: #64748B !important;
        line-height: 1.4 !important;
    }}
    
    /* Style the "Browse files" button */
    div[data-testid="stFileUploadDropzone"] button[kind="secondary"] {{
        background-color: #6366F1 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2) !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
    }}
    
    div[data-testid="stFileUploadDropzone"] button[kind="secondary"]:hover {{
        background-color: #4F46E5 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(99, 102, 241, 0.3) !important;
    }}
    
    div[data-testid="stFileUploadDropzone"] button[kind="secondary"]:focus-visible {{
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.4) !important;
    }}
    
    /* Hide the default file type/size caption and replace with our custom one */
    div[data-testid="stFileUploadDropzone"] > div:last-child {{
        display: none !important;
    }}
    
    /* Add custom file type/size caption */
    div[data-testid="stFileUploadDropzoneInstructions"]::after {{
        content: "Limit {max_size_mb}MB per file • {types_str}" !important;
        font-size: 0.75rem !important;
        font-weight: 400 !important;
        color: #64748B !important;
        line-height: 1.4 !important;
        margin-top: 4px !important;
        display: block !important;
    }}
    
    /* Responsive: Stack on mobile */
    @media (max-width: 640px) {{
        div[data-testid="stFileUploadDropzone"] {{
            flex-direction: column !important;
            align-items: stretch !important;
            gap: 12px !important;
            padding: 16px !important;
        }}
        
        div[data-testid="stFileUploadDropzone"] button[kind="secondary"] {{
            width: 100% !important;
            text-align: center !important;
        }}
    }}
    
    /* Focus visible for accessibility */
    div[data-testid="stFileUploadDropzone"]:focus-within {{
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
    }}
    
    /* File selected state */
    div[data-testid="stFileUploader"].has-file section[data-testid="stFileUploadDropzone"] {{
        border-style: solid !important;
        border-color: #6366F1 !important;
        background-color: #EEF2FF !important;
    }}
    """
    
    st.markdown(css, unsafe_allow_html=True)


def file_uploader(
    label: str = "Upload file",
    help_text: str = "Limit 200MB per file • PDF, DOCX, TXT",
    accepted_types: Optional[List[str]] = None,
    max_size_mb: int = 200,
    key: Optional[str] = None,
    on_change: Optional[Callable] = None,
    disabled: bool = False,
    multiple: bool = False,
) -> Any:
    """
    Render a clean file uploader component using Streamlit's native file_uploader
    with custom styling via CSS injection.
    
    Args:
        label: Accessible label for the file uploader (required for accessibility)
        help_text: Help text with size limit and allowed types
        accepted_types: List of accepted file extensions (e.g., ["pdf", "docx", "txt"])
        max_size_mb: Maximum file size in MB
        key: Unique key for the component
        on_change: Callback when file is selected
        disabled: Whether the uploader is disabled
        multiple: Whether to accept multiple files
    
    Returns:
        Uploaded file(s) or None
    """
    # Generate a unique key if not provided
    if key is None:
        key = f"file_uploader_{uuid.uuid4().hex[:8]}"
    
    # Build dynamic help text if not provided
    if help_text == "Limit 200MB per file • PDF, DOCX, TXT" and accepted_types:
        types_str = ", ".join([t.upper() for t in accepted_types])
        help_text = f"Limit {max_size_mb}MB per file • {types_str}"
    
    # Container with custom CSS class for styling
    with st.container():
        st.markdown(
            f'<div class="hirepilot-file-uploader-wrapper" data-key="{key}" data-max-size="{max_size_mb}">',
            unsafe_allow_html=True
        )
        
        # Inject custom CSS for this specific uploader instance
        _inject_uploader_css(key, max_size_mb, accepted_types)
        
        # Native file uploader with proper label for accessibility
        uploaded_file = st.file_uploader(
            label=label,  # Non-empty label for accessibility
            type=accepted_types,
            accept_multiple_files=multiple,
            key=f"{key}_native",
            on_change=on_change,
            disabled=disabled,
            label_visibility="collapsed",  # Hide label visually but keep for accessibility
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return uploaded_file


def file_uploader_simple(
    label: str = "Drag and drop file here",
    accepted_types: Optional[List[str]] = None,
    max_size_mb: int = 200,
    key: Optional[str] = None,
    on_change: Optional[Callable] = None,
    disabled: bool = False,
    multiple: bool = False,
) -> Any:
    """
    Simplified version that auto-generates help text from accepted_types.
    """
    if accepted_types:
        types_str = ", ".join([t.upper() for t in accepted_types])
        help_text = f"Limit {max_size_mb}MB per file • {types_str}"
    else:
        help_text = f"Limit {max_size_mb}MB per file"
    
    return file_uploader(
        label=label,
        help_text=help_text,
        accepted_types=accepted_types,
        max_size_mb=max_size_mb,
        key=key,
        on_change=on_change,
        disabled=disabled,
        multiple=multiple,
    )