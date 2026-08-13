import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.session import get_db_session
from backend.models.entities import HRUser
from backend.api.routes.auth import get_password_hash
from sqlalchemy.future import select

async def seed_admin():
    async with get_db_session() as db:
        # Check if exists
        stmt = select(HRUser).where(HRUser.email == "admin@hirepilot.com")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            new_user = HRUser(
                email="admin@hirepilot.com",
                password_hash=get_password_hash("admin123"),
                name="System Admin",
            )
            db.add(new_user)
            await db.commit()
            print("Successfully created admin@hirepilot.com user with password: admin123")
        else:
            user.password_hash = get_password_hash("admin123")
            await db.commit()
            print("User admin@hirepilot.com already existed. Reset password to admin123.")

if __name__ == "__main__":
    asyncio.run(seed_admin())
