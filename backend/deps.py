"""
FastAPI dependencies for 1st 4 Mobile Backend.

Provides reusable dependency injection helpers.
"""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db as _get_db
from backend.models import Client


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async database session dependency."""
    async for session in _get_db():
        yield session


async def get_client_or_404(
    client_id: str,
    db: AsyncSession = Depends(get_db),
) -> Client:
    """Fetch a client by UUID string or raise 404."""
    try:
        import uuid
        uid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid client_id format: {client_id}",
        )

    result = await db.execute(select(Client).where(Client.id == uid))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {client_id} not found",
        )
    return client
