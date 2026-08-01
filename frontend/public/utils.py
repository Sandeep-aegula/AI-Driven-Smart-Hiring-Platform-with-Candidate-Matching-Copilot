import os
import streamlit as st

def inject_public_css():
    """Inject the public portal CSS into the Streamlit page.
    This reads `frontend/public/styles/public_portal.css` relative to this file.
    """
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "styles", "public_portal.css")
    # Resolve any relative components (..)
    css_path = os.path.abspath(css_path)
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("Public portal CSS not found.")
