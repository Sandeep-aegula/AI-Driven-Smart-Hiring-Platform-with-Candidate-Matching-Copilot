import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.session import get_db_session
from backend.models.entities import HRUser
from backend.api.routes.auth import get_password_hash
from sqlalchemy.future import select

ADMIN_EMAIL = "hr@gmail.com"
ADMIN_PASSWORD = "123456"


async def seed_admin():
    async with get_db_session() as db:
        # Check if exists
        stmt = select(HRUser).where(HRUser.email == ADMIN_EMAIL)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            new_user = HRUser(
                email=ADMIN_EMAIL,
                password_hash=get_password_hash(ADMIN_PASSWORD),
                name="System Admin",
            )
            db.add(new_user)
            await db.commit()
            print(f"Successfully created {ADMIN_EMAIL} user with password: {ADMIN_PASSWORD}")
        else:
            user.password_hash = get_password_hash(ADMIN_PASSWORD)
            await db.commit()
            print(f"User {ADMIN_EMAIL} already existed. Reset password to {ADMIN_PASSWORD}.")

if __name__ == "__main__":
    asyncio.run(seed_admin())
