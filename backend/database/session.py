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

if not DATABASE_URL.startswith("mysql+aiomysql://"):
    raise RuntimeError(
        "DATABASE_URL must use the MySQL async driver format: "
        "mysql+aiomysql://USER:PASSWORD@HOST:PORT/DATABASE"
    )

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    # NOTE: pool_pre_ping is intentionally left off. The installed
    # aiomysql (0.3.2) + SQLAlchemy (2.0.51) combination has a signature
    # mismatch on the async ping path (AsyncAdapt_aiomysql_connection.ping()
    # missing 1 required positional argument: 'reconnect'), so pre_ping
    # crashes checkout with a TypeError instead of validating the
    # connection. pool_recycle below already bounds how long a connection
    # can go stale, which covers the case pre_ping exists for.
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