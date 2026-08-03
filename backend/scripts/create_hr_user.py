import asyncio

import sys

import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.session import get_db_session

from backend.models.entities import HRUser

from backend.api.routes.auth import get_password_hash  # adjust import path if auth.py lives elsewhere

async def create_hr_user(email: str, password: str, name: str):

    async with get_db_session() as db:

        user = HRUser(

            email=email,

            password_hash=get_password_hash(password),

            name=name,

        )

        db.add(user)

        await db.commit()

        print(f"Created HR user: {email}")

if __name__ == "__main__":

    asyncio.run(create_hr_user(

        email="hr@gmail.com",

        password="123456",

        name="HR Admin",

    ))