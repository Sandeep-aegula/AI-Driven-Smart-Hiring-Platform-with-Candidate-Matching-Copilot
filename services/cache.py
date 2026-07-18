"""
services/cache.py — Unified HirePilot Cache Layer Redirector
============================================================
Routes all caching and invalidation calls through frontend.services.cache
so that all modules share the exact same Streamlit cache instances.
"""

from frontend.services.cache import *
