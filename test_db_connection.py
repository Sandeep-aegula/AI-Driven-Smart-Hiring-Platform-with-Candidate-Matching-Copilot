import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from backend.database.session import engine


async def test_database_connection():

    try:

        async with engine.connect() as connection:

            result = await connection.execute(
                text(
                    """
                    SELECT
                        DATABASE() AS database_name,
                        VERSION() AS mysql_version,
                        CURRENT_USER() AS connected_user
                    """
                )
            )

            row = result.mappings().first()

            print("MySQL connection successful")
            print(
                f"Database: {row['database_name']}"
            )
            print(
                f"MySQL version: {row['mysql_version']}"
            )
            print(
                f"Connected user: "
                f"{row['connected_user']}"
            )

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(
        test_database_connection()
    )