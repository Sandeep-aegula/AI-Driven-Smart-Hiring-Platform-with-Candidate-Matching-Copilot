"""
Safe incremental MySQL schema updates for existing HirePilot databases.

Alembic is not configured in this project. This module adds missing columns
without dropping tables or deleting data.
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text

from backend.database.session import engine

logger = logging.getLogger(__name__)

# (column_name, MySQL ADD COLUMN DDL fragment)
JOB_COLUMN_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("benefits", "benefits JSON NULL"),
    ("openings", "openings INT NOT NULL DEFAULT 1"),
    ("work_mode", "work_mode VARCHAR(50) NOT NULL DEFAULT 'Remote'"),
    ("required_skills", "required_skills JSON NULL"),
    ("technical_skills", "technical_skills JSON NULL"),
    ("soft_skills", "soft_skills JSON NULL"),
    ("qualifications", "qualifications JSON NULL"),
    ("additional_requirements", "additional_requirements JSON NULL"),
    ("experience_required", "experience_required VARCHAR(120) NOT NULL DEFAULT ''"),
    ("salary_range", "salary_range VARCHAR(120) NOT NULL DEFAULT ''"),
    ("published_at", "published_at DATETIME NULL"),
    ("interview_rounds", "interview_rounds INT NOT NULL DEFAULT 1"),
)

APPLICATION_COLUMN_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("source", "source VARCHAR(80) NOT NULL DEFAULT 'careers_page'"),
    ("cover_letter", "cover_letter TEXT NULL"),
    ("reviewed_at", "reviewed_at DATETIME NULL"),
    ("reviewed_by", "reviewed_by VARCHAR(200) NOT NULL DEFAULT ''"),
    ("final_decision", "final_decision VARCHAR(50) NOT NULL DEFAULT ''"),
    ("final_decision_at", "final_decision_at DATETIME NULL"),
    ("final_selected_by", "final_selected_by VARCHAR(200) NOT NULL DEFAULT ''"),
    ("current_stage", "current_stage VARCHAR(100) NOT NULL DEFAULT 'Applied'"),
)

CANDIDATE_COLUMN_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("current_company", "current_company VARCHAR(200) NOT NULL DEFAULT ''"),
)

COMMUNICATION_COLUMN_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("error_message", "error_message TEXT NULL"),
    ("interview_id", "interview_id INT NULL"),
    ("communication_type", "communication_type VARCHAR(100) NOT NULL DEFAULT 'interview_invitation'"),
    ("generated_at", "generated_at DATETIME NULL"),
)

EMPLOYEE_COLUMN_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("application_id", "application_id INT NULL"),
    ("job_id", "job_id INT NULL"),
    ("onboarding_id", "onboarding_id INT NULL"),
)

ONBOARDING_COLUMN_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("selected_at", "selected_at DATETIME NULL"),
    ("ready_for_onboarding", "ready_for_onboarding TINYINT(1) NOT NULL DEFAULT 0"),
)

INTERVIEW_COLUMN_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("application_id", "application_id INTEGER NULL"),
    ("round_number", "round_number INT NOT NULL DEFAULT 1"),
    ("interviewer_email", "interviewer_email VARCHAR(255) NOT NULL DEFAULT ''"),
    ("timezone", "timezone VARCHAR(80) NOT NULL DEFAULT 'UTC'"),
    ("location", "location VARCHAR(255) NULL"),
    ("instructions", "instructions TEXT NULL"),
    ("interviewer_designation", "interviewer_designation VARCHAR(120) NOT NULL DEFAULT ''"),
    ("invitation_email_status", "invitation_email_status VARCHAR(50) NOT NULL DEFAULT 'pending'"),
    ("invitation_sent_at", "invitation_sent_at DATETIME NULL"),
)


async def _ensure_columns(table_name: str, migrations: tuple[tuple[str, str], ...]) -> None:
    async with engine.begin() as conn:
        existing_columns = await conn.run_sync(
            lambda sync_conn: {
                column["name"]
                for column in inspect(sync_conn).get_columns(table_name)
            }
        )
        for column_name, ddl in migrations:
            if column_name in existing_columns:
                continue
            logger.info("Adding missing %s.%s column", table_name, column_name)
            await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))
            existing_columns.add(column_name)


async def ensure_jobs_schema() -> None:
    """Add any missing Job columns on an existing MySQL jobs table."""
    await _ensure_columns("jobs", JOB_COLUMN_MIGRATIONS)


async def ensure_communications_schema() -> None:
    """Add missing communication tracking columns on existing MySQL tables."""
    await _ensure_columns("communications", COMMUNICATION_COLUMN_MIGRATIONS)


async def ensure_employee_schema() -> None:
    """Add missing employee relationship columns on existing MySQL tables."""
    await _ensure_columns("employees", EMPLOYEE_COLUMN_MIGRATIONS)


ONBOARDING_TABLE_MIGRATIONS = """
-- Onboarding tables for HirePilot
-- Safe to run multiple times - only creates tables if they don't exist

CREATE TABLE IF NOT EXISTS `onboardings` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `candidate_id` INT NOT NULL,
    `application_id` INT NOT NULL,
    `job_id` INT NOT NULL,
    `department` VARCHAR(120) NOT NULL DEFAULT '',
    `designation` VARCHAR(120) NOT NULL DEFAULT '',
    `joining_date` VARCHAR(50) NOT NULL DEFAULT '',
    `selected_at` DATETIME(6) NULL,
    `status` VARCHAR(50) NOT NULL DEFAULT 'Pending',
    `ready_for_onboarding` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `completed_at` DATETIME(6) NULL,
    PRIMARY KEY (`id`),
    KEY `idx_onboardings_candidate` (`candidate_id`),
    KEY `idx_onboardings_application` (`application_id`),
    KEY `idx_onboardings_job` (`job_id`),
    KEY `idx_onboardings_status` (`status`),
    CONSTRAINT `fk_onboardings_candidate` FOREIGN KEY (`candidate_id`) REFERENCES `candidates` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_onboardings_application` FOREIGN KEY (`application_id`) REFERENCES `applications` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_onboardings_job` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `onboarding_document_requirements` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `onboarding_id` INT NOT NULL,
    `document_type` VARCHAR(80) NOT NULL,
    `document_name` VARCHAR(200) NOT NULL,
    `required` TINYINT(1) NOT NULL DEFAULT 1,
    `display_order` INT NOT NULL DEFAULT 0,
    `is_custom` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (`id`),
    KEY `idx_requirements_onboarding` (`onboarding_id`),
    CONSTRAINT `fk_requirements_onboarding` FOREIGN KEY (`onboarding_id`) REFERENCES `onboardings` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `onboarding_documents` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `onboarding_id` INT NOT NULL,
    `requirement_id` INT NOT NULL,
    `version` INT NOT NULL DEFAULT 1,
    `original_filename` VARCHAR(255) NOT NULL,
    `stored_filename` VARCHAR(255) NOT NULL,
    `storage_path` VARCHAR(500) NOT NULL,
    `mime_type` VARCHAR(120) NOT NULL DEFAULT '',
    `file_size` INT NOT NULL DEFAULT 0,
    `status` VARCHAR(50) NOT NULL DEFAULT 'Uploaded',
    `rejection_reason` TEXT NULL,
    `reupload_message` TEXT NULL,
    `uploaded_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `verified_at` DATETIME(6) NULL,
    `verified_by` VARCHAR(200) NOT NULL DEFAULT '',
    `rejected_at` DATETIME(6) NULL,
    `rejected_by` VARCHAR(200) NOT NULL DEFAULT '',
    `is_current` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (`id`),
    KEY `idx_documents_onboarding` (`onboarding_id`),
    KEY `idx_documents_requirement` (`requirement_id`),
    KEY `idx_documents_status` (`status`),
    KEY `idx_documents_version` (`version`),
    CONSTRAINT `fk_documents_onboarding` FOREIGN KEY (`onboarding_id`) REFERENCES `onboardings` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_documents_requirement` FOREIGN KEY (`requirement_id`) REFERENCES `onboarding_document_requirements` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


async def ensure_workflow_schema() -> None:
    """Add workflow columns and rely on create_all for new tables."""
    await ensure_jobs_schema()
    await ensure_communications_schema()
    await ensure_employee_schema()
    tables = await _existing_tables()
    if "applications" in tables:
        await _ensure_columns("applications", APPLICATION_COLUMN_MIGRATIONS)
    if "candidates" in tables:
        await _ensure_columns("candidates", CANDIDATE_COLUMN_MIGRATIONS)
    if "interviews" in tables:
        await _ensure_columns("interviews", INTERVIEW_COLUMN_MIGRATIONS)


async def ensure_onboarding_schema() -> None:
    """Create onboarding tables if they don't exist."""
    async with engine.begin() as conn:
        # Create onboardings table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS `onboardings` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `candidate_id` INT NOT NULL,
                `application_id` INT NOT NULL,
                `job_id` INT NOT NULL,
                `department` VARCHAR(120) NOT NULL DEFAULT '',
                `designation` VARCHAR(120) NOT NULL DEFAULT '',
                `joining_date` VARCHAR(50) NOT NULL DEFAULT '',
                `selected_at` DATETIME(6) NULL,
                `status` VARCHAR(50) NOT NULL DEFAULT 'Pending',
                `ready_for_onboarding` TINYINT(1) NOT NULL DEFAULT 0,
                `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                `completed_at` DATETIME(6) NULL,
                PRIMARY KEY (`id`),
                KEY `idx_onboardings_candidate` (`candidate_id`),
                KEY `idx_onboardings_application` (`application_id`),
                KEY `idx_onboardings_job` (`job_id`),
                KEY `idx_onboardings_status` (`status`),
                CONSTRAINT `fk_onboardings_candidate` FOREIGN KEY (`candidate_id`) REFERENCES `candidates` (`id`) ON DELETE CASCADE,
                CONSTRAINT `fk_onboardings_application` FOREIGN KEY (`application_id`) REFERENCES `applications` (`id`) ON DELETE CASCADE,
                CONSTRAINT `fk_onboardings_job` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))

        # Create onboarding_document_requirements table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS `onboarding_document_requirements` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `onboarding_id` INT NOT NULL,
                `document_type` VARCHAR(80) NOT NULL,
                `document_name` VARCHAR(200) NOT NULL,
                `required` TINYINT(1) NOT NULL DEFAULT 1,
                `display_order` INT NOT NULL DEFAULT 0,
                `is_custom` TINYINT(1) NOT NULL DEFAULT 0,
                `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                PRIMARY KEY (`id`),
                KEY `idx_requirements_onboarding` (`onboarding_id`),
                CONSTRAINT `fk_requirements_onboarding` FOREIGN KEY (`onboarding_id`) REFERENCES `onboardings` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))

        # Create onboarding_documents table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS `onboarding_documents` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `onboarding_id` INT NOT NULL,
                `requirement_id` INT NOT NULL,
                `version` INT NOT NULL DEFAULT 1,
                `original_filename` VARCHAR(255) NOT NULL,
                `stored_filename` VARCHAR(255) NOT NULL,
                `storage_path` VARCHAR(500) NOT NULL,
                `mime_type` VARCHAR(120) NOT NULL DEFAULT '',
                `file_size` INT NOT NULL DEFAULT 0,
                `status` VARCHAR(50) NOT NULL DEFAULT 'Uploaded',
                `rejection_reason` TEXT NULL,
                `reupload_message` TEXT NULL,
                `uploaded_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                `verified_at` DATETIME(6) NULL,
                `verified_by` VARCHAR(200) NOT NULL DEFAULT '',
                `rejected_at` DATETIME(6) NULL,
                `rejected_by` VARCHAR(200) NOT NULL DEFAULT '',
                `is_current` TINYINT(1) NOT NULL DEFAULT 1,
                `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                PRIMARY KEY (`id`),
                KEY `idx_documents_onboarding` (`onboarding_id`),
                KEY `idx_documents_requirement` (`requirement_id`),
                KEY `idx_documents_status` (`status`),
                KEY `idx_documents_version` (`version`),
                CONSTRAINT `fk_documents_onboarding` FOREIGN KEY (`onboarding_id`) REFERENCES `onboardings` (`id`) ON DELETE CASCADE,
                CONSTRAINT `fk_documents_requirement` FOREIGN KEY (`requirement_id`) REFERENCES `onboarding_document_requirements` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))

        await _ensure_columns("onboardings", ONBOARDING_COLUMN_MIGRATIONS)
        await _ensure_columns("onboarding_document_requirements", (("required", "required TINYINT(1) NOT NULL DEFAULT 1"),))

        # Ensure default document requirements exist for each onboarding
        await conn.execute(text("""
            INSERT INTO `onboarding_document_requirements`
                (`onboarding_id`, `document_type`, `document_name`, `required`, `display_order`, `is_custom`)
            SELECT
                o.id, 'Government ID', 'Government ID', TRUE, 1, FALSE
            FROM `onboardings` o
            WHERE NOT EXISTS (
                SELECT 1 FROM `onboarding_document_requirements` r
                WHERE r.`onboarding_id` = o.id AND r.`document_type` = 'Government ID'
            );
        """))


async def _existing_tables() -> set[str]:
    async with engine.connect() as conn:
        return set(
            await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
        )


async def ensure_interview_application_id_not_null() -> None:
    """
    Enforce NOT NULL constraint on interviews.application_id and add foreign key.
    This should only be run AFTER all orphaned interviews have been repaired.
    """
    async with engine.begin() as conn:
        # Check if column exists and is nullable
        result = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_columns("interviews")
        )
        app_id_col = next((c for c in result if c["name"] == "application_id"), None)
        
        if not app_id_col:
            logger.warning("interviews.application_id column does not exist, skipping NOT NULL enforcement")
            return
        
        # Check if already NOT NULL
        if not app_id_col.get("nullable", True):
            logger.info("interviews.application_id is already NOT NULL")
        else:
            # First, verify no NULL values remain
            null_count_result = await conn.execute(text(
                "SELECT COUNT(*) FROM `interviews` WHERE `application_id` IS NULL"
            ))
            null_count = null_count_result.scalar()
            
            if null_count > 0:
                raise RuntimeError(
                    f"Cannot enforce NOT NULL: {null_count} interviews still have NULL application_id. "
                    "Run the repair script first."
                )
            
            # Alter column to NOT NULL
            logger.info("Altering interviews.application_id to NOT NULL")
            await conn.execute(text(
                "ALTER TABLE `interviews` MODIFY COLUMN `application_id` INTEGER NOT NULL"
            ))
            logger.info("Successfully set interviews.application_id to NOT NULL")
        
        # Check if foreign key exists
        fk_result = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_foreign_keys("interviews")
        )
        has_fk = any(
            fk.get("constrained_columns") == ["application_id"] 
            and fk.get("referred_table") == "applications"
            for fk in fk_result
        )
        
        if not has_fk:
            logger.info("Adding foreign key constraint on interviews.application_id -> applications.id")
            await conn.execute(text("""
                ALTER TABLE `interviews` 
                ADD CONSTRAINT `fk_interviews_application` 
                FOREIGN KEY (`application_id`) REFERENCES `applications` (`id`) ON DELETE CASCADE
            """))
            logger.info("Successfully added foreign key constraint on interviews.application_id")
        else:
            logger.info("Foreign key constraint on interviews.application_id already exists")


async def ensure_all_schemas() -> None:
    """Run all schema migrations in order."""
    await ensure_workflow_schema()
    await ensure_onboarding_schema()
    await ensure_interview_application_id_not_null()
