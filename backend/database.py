"""
SQLAlchemy async database setup for 1st 4 Mobile Backend.

Uses asyncpg for async PostgreSQL access.
Connection: postgresql+asyncpg://free33@localhost:5432/first4mobile
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger("1st4backend.database")

DATABASE_URL = "postgresql+asyncpg://free33@localhost:5432/first4mobile"

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


async def init_db() -> None:
    """Create all tables if they don't exist."""
    from backend.models import (  # noqa: F401 — ensure models are imported before create_all
        Client,
        UploadedFile,
        AuditResult,
        Dispute,
        Invoice,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created / verified")
