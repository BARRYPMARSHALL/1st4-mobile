"""
SQLAlchemy ORM models for 1st 4 Mobile Backend.

Defines:
  - Client
  - UploadedFile
  - AuditResult
  - Dispute
  - Invoice

All use UUID primary keys and proper foreign key relationships.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base


# ── Enum Types ─────────────────────────────────────────────────────


class ClientStatus(str, enum.Enum):
    registered = "registered"
    authorized = "authorized"
    files_uploaded = "files_uploaded"
    audit_running = "audit_running"
    audit_complete = "audit_complete"
    dispute_submitted = "dispute_submitted"
    settled = "settled"


class AuditStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    complete = "complete"
    failed = "failed"


class DisputeStatus(str, enum.Enum):
    draft = "draft"
    reviewed = "reviewed"
    submitted_to_carrier = "submitted_to_carrier"
    credit_issued = "credit_issued"


class InvoiceStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"


# ── Helper ─────────────────────────────────────────────────────────


def _utcnow() -> datetime:
    return datetime.utcnow()


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ── Models ─────────────────────────────────────────────────────────


class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    company_name = Column(String(255), nullable=False)
    abn = Column(String(50), nullable=False)
    industry = Column(String(100), nullable=True)
    fleet_size = Column(Integer, nullable=True, default=0)
    primary_carrier = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    status = Column(
        Enum(ClientStatus),
        default=ClientStatus.registered,
        nullable=False,
    )
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    authorized_at = Column(DateTime, nullable=True)
    authorized_by = Column(String(255), nullable=True)

    # Relationships
    uploaded_files = relationship("UploadedFile", back_populates="client", cascade="all, delete-orphan")
    audit_results = relationship("AuditResult", back_populates="client", cascade="all, delete-orphan")
    disputes = relationship("Dispute", back_populates="client", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime, default=_utcnow, nullable=False)
    storage_path = Column(String(500), nullable=False)

    client = relationship("Client", back_populates="uploaded_files")


class AuditResult(Base):
    __tablename__ = "audit_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(
        Enum(AuditStatus),
        default=AuditStatus.pending,
        nullable=False,
    )
    total_flags = Column(Integer, nullable=True, default=0)
    total_monthly_overcharge = Column(Float, nullable=True, default=0.0)
    total_annualised = Column(Float, nullable=True, default=0.0)
    raw_results_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    client = relationship("Client", back_populates="audit_results")
    disputes = relationship("Dispute", back_populates="audit")


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    )
    audit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audit_results.id", ondelete="SET NULL"),
        nullable=True,
    )
    status = Column(
        Enum(DisputeStatus),
        default=DisputeStatus.draft,
        nullable=False,
    )
    dispute_letter_text = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    carrier_name = Column(String(100), nullable=True)
    credit_amount = Column(Float, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    client = relationship("Client", back_populates="disputes")
    audit = relationship("AuditResult", back_populates="disputes")
    invoices = relationship("Invoice", back_populates="dispute", cascade="all, delete-orphan")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    )
    dispute_id = Column(
        UUID(as_uuid=True),
        ForeignKey("disputes.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount = Column(Float, nullable=False, default=0.0)
    status = Column(
        Enum(InvoiceStatus),
        default=InvoiceStatus.pending,
        nullable=False,
    )
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)

    client = relationship("Client", back_populates="invoices")
    dispute = relationship("Dispute", back_populates="invoices")


class User(Base):
    """Partner / admin users who access the owner dashboard."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)


class Booking(Base):
    """Demo booking requests from the Book a Demo page."""
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    employees = Column(String(50), nullable=True)
    date = Column(String(20), nullable=False)   # ISO date string (YYYY-MM-DD)
    time = Column(String(20), nullable=False)   # e.g. "09:00"
    created_at = Column(DateTime, default=_utcnow, nullable=False)
