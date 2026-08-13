from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. "
        "Configure the MySQL connection in the .env file."
    )

SUPPORTED_DRIVERS = ("mysql+aiomysql://", "sqlite+aiosqlite://")

if not DATABASE_URL.startswith(SUPPORTED_DRIVERS):
    raise RuntimeError(
        "DATABASE_URL must use an async driver format, e.g. "
        "mysql+aiomysql://USER:PASSWORD@HOST:PORT/DATABASE or "
        "sqlite+aiosqlite:///PATH/TO/DATABASE.db"
    )

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """
    FastAPI database dependency.
    Provides one AsyncSession per request.
    """

    async with AsyncSessionLocal() as session:
        try:
            yield session

        except Exception:
            await session.rollback()
            raise

        finally:
            await session.close()


@asynccontextmanager
async def get_db_session():
    """
    Database session for services and scripts.
    """

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()

        except Exception:
            await session.rollback()
            raise