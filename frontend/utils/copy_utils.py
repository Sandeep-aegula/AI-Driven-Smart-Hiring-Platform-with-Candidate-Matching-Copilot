"""utils/copy_utils.py - Copy utility functions.

Utility functions for copying content.
"""

import streamlit as st


def copy_button(content: str, button_id: str) -> None:
    """Render a copy button for content."""
    if st.button("📋", key=f"copy_{button_id}", help="Copy to clipboard"):
        st.code(content, language=None)
        st.success("Copied!")
