"""
SQLAlchemy async database setup for 1st 4 Mobile Backend.

Uses asyncpg for async PostgreSQL access.
Connection: postgresql+asyncpg://free33@localhost:5432/first4mobile
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger("1st4backend.database")

import os
from pathlib import Path

# Railway provides DATABASE_URL via Postgres plugin.
# Fall back to local dev database if not set.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://free33@localhost:5432/first4mobile"
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db(max_retries: int = 5, retry_delay: int = 2) -> None:
    """Create all tables if they don't exist.

    Retries up to ``max_retries`` times with ``retry_delay`` seconds
    between attempts.  This gives Railway's Postgres plugin time to
    finish provisioning before the backend connects.

    Raises the last connection error if all retries are exhausted.
    """
    from backend.models import (  # noqa: F401 — ensure models are imported before create_all
        AuditResult,
        Client,
        Dispute,
        Invoice,
        UploadedFile,
    )

    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info(
                "Database tables created / verified "
                f"(attempt {attempt}/{max_retries})"
            )
            return
        except Exception as exc:
            last_error = exc
            logger.warning(
                f"DB connection attempt {attempt}/{max_retries} failed: "
                f"{exc}. Retrying in {retry_delay}s…"
            )
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)

    logger.critical(
        f"Could not connect to database after {max_retries} attempts. "
        f"Last error: {last_error}"
    )
    raise last_error  # type: ignore[misc]
