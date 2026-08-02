"""
Migration script to add the Communication table to the database.

This script creates the communications table for tracking shortlisted candidates
and their email communications in the recruitment workflow.

Run this script once to create the table:
    python -m backend.database.add_communication_table
"""

import asyncio
import logging
from sqlalchemy import text
from backend.database.session import engine, get_db_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_communication_table():
    """Create the communications table."""

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS communications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        candidate_id INT NOT NULL,
        application_id INT NOT NULL,
        job_id INT NOT NULL,
        recruitment_round VARCHAR(200) DEFAULT 'Initial Screening',
        status VARCHAR(50) DEFAULT 'pending',
        email VARCHAR(255) NOT NULL,
        subject VARCHAR(500) DEFAULT '',
        message TEXT,
        error_message TEXT,
        email_template VARCHAR(100) DEFAULT '',
        queued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        sent_at DATETIME NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

        INDEX idx_candidate_id (candidate_id),
        INDEX idx_application_id (application_id),
        INDEX idx_job_id (job_id),
        INDEX idx_status (status),
        INDEX idx_email (email),

        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
        FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    async with get_db_session() as session:
        try:
            logger.info("Creating communications table...")
            await session.execute(text(create_table_sql))
            await session.commit()
            logger.info("✅ Communications table created successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating communications table: {e}")
            await session.rollback()
            return False


async def check_table_exists():
    """Check if the communications table already exists."""
    check_sql = """
    SELECT COUNT(*) as count
    FROM information_schema.tables
    WHERE table_schema = DATABASE()
    AND table_name = 'communications';
    """

    async with get_db_session() as session:
        result = await session.execute(text(check_sql))
        row = result.fetchone()
        return row[0] > 0 if row else False


async def main():
    """Main migration function."""
    logger.info("Starting communication table migration...")

    # Check if table already exists
    exists = await check_table_exists()
    if exists:
        logger.info("⚠️  Communications table already exists. Skipping creation.")
        return

    # Create the table
    success = await create_communication_table()

    if success:
        logger.info("✅ Migration completed successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Restart your FastAPI backend server")
        logger.info("2. Test the shortlist functionality in the Candidate Management page")
        logger.info("3. Check the Communications tab for pending shortlisted candidates")
    else:
        logger.error("❌ Migration failed. Please check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())
