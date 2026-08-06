"""
Cleanup duplicate Communication rows per interview_id.

Keeps the row with the highest id for each interview_id that has duplicates
and deletes the rest.  Idempotent — running twice in a row is safe.

Usage:
    python -m backend.scripts.cleanup_duplicate_communications
"""

import asyncio
import logging

from sqlalchemy import func, select, delete, desc

from backend.database.session import get_db_session
from backend.models.entities import Communication

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup() -> None:
    async with get_db_session() as session:
        # Find interview_ids with more than one Communication row
        stmt = (
            select(
                Communication.interview_id,
                func.count(Communication.id).label("cnt"),
            )
            .where(Communication.interview_id.isnot(None))
            .group_by(Communication.interview_id)
            .having(func.count(Communication.id) > 1)
        )
        result = await session.execute(stmt)
        duplicates = result.all()

        if not duplicates:
            logger.info("No duplicate Communication rows found. Nothing to do.")
            return

        total_interviews_cleaned = 0
        total_rows_deleted = 0

        for interview_id, count in duplicates:
            # Find the row to keep (highest id)
            keep_stmt = (
                select(Communication.id)
                .where(Communication.interview_id == interview_id)
                .order_by(desc(Communication.id))
                .limit(1)
            )
            keep_result = await session.execute(keep_stmt)
            keep_id = keep_result.scalar_one()

            # Delete all other rows for this interview_id
            del_stmt = (
                delete(Communication)
                .where(
                    Communication.interview_id == interview_id,
                    Communication.id != keep_id,
                )
            )
            del_result = await session.execute(del_stmt)
            deleted = del_result.rowcount

            logger.info(
                "interview_id=%s: kept id=%s, deleted %d duplicate(s)",
                interview_id,
                keep_id,
                deleted,
            )
            total_interviews_cleaned += 1
            total_rows_deleted += deleted

        # Session commits automatically via get_db_session context manager

        logger.info(
            "Done. Cleaned %d interview(s), deleted %d total duplicate row(s).",
            total_interviews_cleaned,
            total_rows_deleted,
        )


if __name__ == "__main__":
    asyncio.run(cleanup())
