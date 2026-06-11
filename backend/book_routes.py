"""
Demo booking API routes for 1st 4 Mobile Backend.

Prefix: /api/book
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_db
from backend.models import Booking

logger = logging.getLogger("1st4backend.book_routes")

router = APIRouter(prefix="/api/book", tags=["book"])


# ── Schemas ─────────────────────────────────────────────────────────


class BookingRequest(BaseModel):
    name: str
    email: EmailStr
    company: str
    phone: str | None = None
    employees: str | None = None
    date: str
    time: str

    @field_validator("name", "company")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be empty")
        return v.strip()

    @field_validator("date")
    @classmethod
    def valid_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format")
        return v

    @field_validator("time")
    @classmethod
    def valid_time(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("time must be in HH:MM format")
        return v


class BookingResponse(BaseModel):
    status: str
    message: str
    booking_id: str


# ── Routes ──────────────────────────────────────────────────────────


@router.post("", response_model=BookingResponse, status_code=status.HTTP_200_OK)
async def book_demo(
    body: BookingRequest,
    db: AsyncSession = Depends(get_db),
):
    """Save a demo booking request to the database and log a notification."""

    booking = Booking(
        name=body.name,
        email=body.email,
        company=body.company,
        phone=body.phone,
        employees=body.employees,
        date=body.date,
        time=body.time,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    booking_id_str = str(booking.id)

    # ── Email notification (placeholder) ────────────────────────────
    # TODO: Wire up real SMTP email notification here.
    # For now, log the booking to a file and to the application log.
    _log_booking_notification(booking_id_str, body)

    logger.info(
        "Demo booking saved | id=%s name=%s email=%s company=%s date=%s time=%s",
        booking_id_str,
        body.name,
        body.email,
        body.company,
        body.date,
        body.time,
    )

    return BookingResponse(
        status="ok",
        message="Demo booking confirmed. We'll send a calendar invite shortly.",
        booking_id=booking_id_str,
    )


# ── Helpers ─────────────────────────────────────────────────────────


def _log_booking_notification(booking_id: str, body: BookingRequest) -> None:
    """
    Log the booking to a flat file as a stand-in for email delivery.
    Replace this function with an actual SMTP / SendGrid / SES call in production.
    """
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    notifications_dir = PROJECT_ROOT / "notifications"
    notifications_dir.mkdir(parents=True, exist_ok=True)

    log_path = notifications_dir / "demo_bookings.log"
    line = (
        f"[{datetime.utcnow().isoformat()}] "
        f"BOOKING {booking_id} | "
        f"name={body.name} | "
        f"email={body.email} | "
        f"company={body.company} | "
        f"phone={body.phone or 'N/A'} | "
        f"employees={body.employees or 'N/A'} | "
        f"date={body.date} | "
        f"time={body.time}\n"
    )
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)

    logger.info(
        "Booking notification logged to %s (TODO: replace with real email)",
        log_path,
    )
