"""Migration: Add invitation tracking fields to interviews table."""
from __future__ import annotations

import logging
from alembic import op
from sqlalchemy import text

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


def upgrade() -> None:
    bind = op.get_bind()
    for column_name, column_def in COLUMNS:
        try:
            op.execute(
                text(f"ALTER TABLE interviews ADD COLUMN {column_name} {column_def}")
            )
            logger.info("Added column interviews.%s", column_name)
        except Exception as exc:  # pragma: no cover - best-effort migration
            logger.warning("Skipping column %s: %s", column_name, exc)


def downgrade() -> None:
    bind = op.get_bind()
    for column_name, _ in COLUMNS:
        try:
            op.execute(text(f"ALTER TABLE interviews DROP COLUMN {column_name}"))
            logger.info("Dropped column interviews.%s", column_name)
        except Exception as exc:  # pragma: no cover - best-effort migration
            logger.warning("Skipping drop column %s: %s", column_name, exc)
