"""
Initialize HirePilot MySQL tables from SQLAlchemy models.

Usage:
    python scripts/init_database.py
"""

from __future__ import annotations

import asyncio
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.database.init_db import _run_cli


if __name__ == "__main__":
    asyncio.run(_run_cli())
