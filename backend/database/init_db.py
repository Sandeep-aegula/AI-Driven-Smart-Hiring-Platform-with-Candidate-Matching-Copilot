"""
MySQL database initialization for HirePilot.

Creates all SQLAlchemy model tables and applies incremental schema updates.
Safe to run multiple times — only missing tables/columns are added.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import os

# Add project root to path when run as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import inspect, text

from backend.database.base import Base
from backend.database.session import engine
from backend.database.schema_migrations import ensure_all_schemas

# Import all models so they register on Base.metadata before create_all().
import backend.models.entities  # noqa: F401

logger = logging.getLogger(__name__)


async def initialize_database() -> None:
    """Create missing MySQL tables from registered SQLAlchemy models."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    await ensure_all_schemas()

    async with engine.connect() as connection:
        table_names = await connection.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )

    logger.info("Database initialized with %d tables.", len(table_names))


async def _run_cli() -> None:
    print("Connecting to MySQL...")
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    print("MySQL connection successful.")
    print("Creating missing HirePilot tables...")
    await initialize_database()
    print("Database initialization completed successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run_cli())
