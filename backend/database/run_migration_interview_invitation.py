"""Standalone migration: add invitation tracking fields to interviews table."""
from __future__ import annotations

import sys, os
# Ensure the project root is in PYTHONPATH for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import asyncio
import logging

from backend.database.session import engine

logger = logging.getLogger(__name__)

COLUMNS = [
    ("application_id", "INTEGER NULL"),
    ("round_number", "INTEGER DEFAULT 1 NOT NULL"),
    ("timezone", "VARCHAR(80) DEFAULT 'UTC' NOT NULL"),
    ("instructions", "TEXT NULL"),
    ("interviewer_email", "VARCHAR(255) DEFAULT '' NOT NULL"),
    ("interviewer_designation", "VARCHAR(120) DEFAULT '' NOT NULL"),
    ("invitation_email_status", "VARCHAR(50) DEFAULT 'pending' NOT NULL"),
    ("invitation_sent_at", "DATETIME NULL"),
]


async def migrate() -> None:
    async with engine.begin() as conn:
        for column_name, column_def in COLUMNS:
            try:
                await conn.execute(
                    text(f"ALTER TABLE interviews ADD COLUMN {column_name} {column_def}")
                )
                logger.info("Added column interviews.%s", column_name)
            except Exception as exc:  # pragma: no cover - best-effort migration
                logger.warning("Skipping column %s: %s", column_name, exc)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from sqlalchemy import text
    asyncio.run(migrate())
