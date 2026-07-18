"""
page_utils.py - Shared page utilities for HirePilot
=====================================================
All pages call setup_page() as their first statement after set_page_config().

Performance guarantees:
- CSS is read from disk ONCE per server process (cache_resource)
- CSS is injected into the DOM ONCE per browser session (session_state flag)
- Sidebar brand and footer HTML are static strings — no computation
- FontAwesome is loaded via CDN link (browser caches it after first page)
"""

import os
import streamlit as st


# ---------------------------------------------------------------------------
# CSS — loaded from disk once via cache.py, injected once per session
# ---------------------------------------------------------------------------

def _get_css() -> str:
    """Return the combined CSS string. Reads disk only ONCE per server process."""
    from frontend.services.cache import _load_css_files
    return _load_css_files()


def inject_css_once():
    """
    Inject minimal CSS into the page.
    """
    css = _get_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)



# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

_SIDEBAR_BRAND_HTML = """
<div style="padding: 10px 10px 20px 10px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2E8F0; margin-bottom: 15px;">
    <div style="background: linear-gradient(135deg, #6366F1, #4F46E5); width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 800; color: white; box-shadow: 0 4px 12px rgba(99,102,241,0.35);">
        <i class="fa-solid fa-paper-plane" style="transform: rotate(-10deg);"></i>
    </div>
    <div>
        <div style="font-weight: 800; color: #0F172A; font-size: 1.25rem; letter-spacing: 0.02em; line-height: 1;">HirePilot</div>
        <div style="font-size: 0.7rem; color: #64748B; font-weight: 600; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.05em;">AI RECRUITMENT</div>
    </div>
</div>
"""

_SIDEBAR_FOOTER_HTML = """
<div style="margin-top: 80px; padding: 16px 10px 0 10px; border-top: 1px solid #E2E8F0;">
    <div style="display: flex; align-items: center; gap: 10px; opacity: 0.85;">
        <div style="background-color: #F1F5F9; width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #6366F1;">
            <i class="fa-solid fa-rocket"></i>
        </div>
        <div>
            <div style="font-weight: 700; color: #0F172A; font-size: 0.78rem;">HirePilot v1.2</div>
            <div style="font-size: 0.65rem; color: #64748B;">Plan: Enterprise</div>
        </div>
    </div>
</div>
"""


def render_sidebar_brand():
    """Render the HirePilot sidebar brand header (static HTML, no recomputation)."""
    with st.sidebar:
        st.markdown(_SIDEBAR_BRAND_HTML, unsafe_allow_html=True)


def render_sidebar_footer():
    """Render the HirePilot sidebar version footer (static HTML)."""
    with st.sidebar:
        st.markdown(_SIDEBAR_FOOTER_HTML, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

def render_page_header(title: str, subtitle: str):
    """Render the page title + subtitle + divider."""
    st.markdown(
        f"""<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
        <div>
            <h1 style="font-size: 1.6rem; font-weight: 800; color: #0F172A; margin: 0; line-height: 1.2;">{title}</h1>
            <p style="font-size: 0.85rem; color: #64748B; margin: 2px 0 0 0; font-weight: 500;">{subtitle}</p>
        </div>
    </div>
    <hr style="margin: 8px 0 20px 0; border-color: #F1F5F9;">""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# State initialisation
# ---------------------------------------------------------------------------

def _init_state():
    """Initialise global session state on first call. Safe to call multiple times."""
    from frontend.services.app_state import AppState
    AppState.init()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def setup_page(title: str, subtitle: str, **kwargs):
    """
    One-liner page setup called at the top of every page.

    Execution order:
      1. Init session state (no-op if already done)
      2. Inject CSS (no-op if already injected this session)
      3. Render sidebar brand
      4. Render page header
      5. Render sidebar footer
    """
    _init_state()
    inject_css_once()
    render_sidebar_brand()
    render_page_header(title, subtitle)
    render_sidebar_footer()
