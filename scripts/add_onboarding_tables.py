import asyncio

from backend.database.base import Base
from backend.database.session import engine
from backend.models.entities import Onboarding, OnboardingDocument, OnboardingDocumentRequirement


async def create_onboarding_tables():
    """
    Asynchronously creates the onboarding-related tables in the database.
    """
    print("Creating onboarding tables...")
    async with engine.begin() as conn:
        # The following tables will be created:
        # - onboarding
        # - onboarding_document_requirements
        # - onboarding_documents
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[
                Onboarding.__table__,
                OnboardingDocumentRequirement.__table__,
                OnboardingDocument.__table__,
            ],
            checkfirst=True,  # This prevents an error if the tables already exist
        )
    print("Onboarding tables created successfully.")


if __name__ == "__main__":
    asyncio.run(create_onboarding_tables())
