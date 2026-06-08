"""
Client-facing API routes for 1st 4 Mobile Backend.

Prefix: /api/client

Refactored from the original server.py monolith.
"""

import base64
import json
import logging
import os
import re
import shutil
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_db, get_client_or_404
from backend.loa_template import get_loa_text
from backend.models import (
    Client,
    ClientStatus,
    AuditResult,
    AuditStatus,
    UploadedFile,
)

logger = logging.getLogger("1st4backend.client_routes")

router = APIRouter(prefix="/api/client", tags=["client"])

# ── Project paths ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WWW_DIR = PROJECT_ROOT / "www"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
OUTPUT_DIR = PROJECT_ROOT / "output"

ALLOWED_EXTENSIONS = {".csv", ".pdf", ".xlsx", ".xls"}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB


def _validate_file(upload_file: UploadFile) -> None:
    """Validate file extension and size."""
    ext = Path(upload_file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )


# ── POST /api/client/register ──────────────────────────────────────


@router.post("/register")
async def register_client(request: Request, db: AsyncSession = Depends(get_db)):
    """Register a new client and return a Letter of Authority."""
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    required = ["company_name", "abn"]
    for field in required:
        if not data.get(field):
            raise HTTPException(
                status_code=400,
                detail=f"Missing required field: '{field}'",
            )

    client = Client(
        company_name=data["company_name"],
        abn=data["abn"],
        industry=data.get("industry", ""),
        fleet_size=data.get("fleet_size", 0),
        primary_carrier=data.get("primary_carrier", "Telstra"),
        email=data.get("email", ""),
        status=ClientStatus.registered,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)

    carrier = data.get("primary_carrier", "Telstra")
    loa_text = get_loa_text(
        company_name=data["company_name"],
        abn=data["abn"],
        carrier=carrier,
    )

    logger.info(f"Registered client {client.id}: {data['company_name']} ({carrier})")
    return {
        "status": "ok",
        "client_id": str(client.id),
        "loa_text": loa_text,
    }


# ── POST /api/client/{client_id}/authorize ─────────────────────────


@router.post("/{client_id}/authorize")
async def authorize_client(
    client_id: str,
    request: Request,
    client: Client = Depends(get_client_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Authorise 1st 4 Mobile to act on behalf of a client."""
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    signature_data = data.get("signature_data")
    signed_by = data.get("signed_by")

    if not signature_data or not signed_by:
        raise HTTPException(
            status_code=400,
            detail="Both 'signature_data' (base64 PNG) and 'signed_by' are required",
        )

    # Save signature PNG
    if signature_data.startswith("data:image/png;base64,"):
        signature_data = signature_data.replace("data:image/png;base64,", "")
    elif signature_data.startswith("data:"):
        signature_data = re.sub(r"^data:[^;]+;base64,", "", signature_data)

    client_upload_dir = UPLOADS_DIR / client_id
    client_upload_dir.mkdir(parents=True, exist_ok=True)

    sig_path = client_upload_dir / "signature.png"
    try:
        padding = 4 - len(signature_data) % 4
        if padding != 4:
            signature_data += "=" * padding
        sig_bytes = base64.b64decode(signature_data)
        with open(sig_path, "wb") as f:
            f.write(sig_bytes)
        logger.info(f"Saved signature for client {client_id} to {sig_path}")
    except Exception as exc:
        logger.error(f"Failed to decode/save signature for {client_id}: {exc}")
        raise HTTPException(status_code=400, detail=f"Failed to process signature: {exc}")

    # Update client
    client.status = ClientStatus.authorized
    client.authorized_by = signed_by
    client.authorized_at = datetime.utcnow()
    await db.commit()

    return {
        "status": "ok",
        "authorized": True,
        "signed_by": signed_by,
    }


# ── POST /api/upload ───────────────────────────────────────────────


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a billing file for a client."""
    # Validate client exists
    try:
        client_uuid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client_id format")

    client = await db.get(Client, client_uuid)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    # Validate file
    _validate_file(file)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds maximum size of 200 MB")

    # Save to disk
    file_uuid = str(uuid.uuid4())
    client_dir = UPLOADS_DIR / client_id
    client_dir.mkdir(parents=True, exist_ok=True)
    dest = client_dir / (file.filename or f"upload_{file_uuid}")
    with open(dest, "wb") as f:
        f.write(content)

    # Record in DB
    ext = Path(file.filename or "").suffix.lower()
    uploaded = UploadedFile(
        client_id=client_uuid,
        filename=file.filename or f"upload_{file_uuid}",
        file_size=len(content),
        file_type=ext.lstrip("."),
        storage_path=str(dest),
    )
    db.add(uploaded)

    # Update client status if appropriate
    if client.status == ClientStatus.authorized:
        client.status = ClientStatus.files_uploaded

    await db.commit()

    logger.info(f"Uploaded {file.filename} ({len(content)} bytes) for client {client_id} → {dest}")
    return {
        "status": "ok",
        "file_id": file_uuid,
        "filename": file.filename,
        "size_bytes": len(content),
    }


# ── GET /api/client/{client_id}/results ────────────────────────────


@router.get("/{client_id}/results")
async def get_results_api(
    client: Client = Depends(get_client_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Return the latest audit results for a client."""
    result = await db.execute(
        select(AuditResult)
        .where(AuditResult.client_id == client.id)
        .order_by(AuditResult.created_at.desc())
        .limit(1)
    )
    audit = result.scalar_one_or_none()

    if not audit:
        raise HTTPException(
            status_code=404,
            detail="No audit results found. Run an audit first.",
        )

    return {
        "status": "ok",
        "client_id": str(client.id),
        "client_name": client.company_name,
        "results": {
            "status": audit.status.value if audit.status else None,
            "total_flags": audit.total_flags,
            "total_monthly_overcharge": audit.total_monthly_overcharge,
            "total_annualised": audit.total_annualised,
            "raw_results": audit.raw_results_json,
            "created_at": audit.created_at.isoformat() if audit.created_at else None,
            "completed_at": audit.completed_at.isoformat() if audit.completed_at else None,
        },
    }


# ── GET /api/client/{client_id}/dashboard ──────────────────────────


def _extract_dashboard_data(audit: AuditResult, client: Client) -> dict:
    """Transform audit results into dashboard-friendly format."""
    raw = audit.raw_results_json or {}
    summary = raw.get("pipeline_summary", {})

    total_monthly = float(summary.get("total_monthly_overcharge", 0.0))
    total_annualised = float(summary.get("total_annualised", total_monthly * 12))
    total_flags = int(summary.get("total_flags", 0))

    breakdown = summary.get("breakdown", {})

    engine_names = {
        "ghost_lines": "Ghost Lines",
        "rate_mismatches": "Rate Mismatches",
        "roaming": "Roaming Anomalies",
        "legacy_rollbacks": "Legacy Rollbacks",
        "duplicates": "Duplicate Services",
    }

    monthly_breakdown = summary.get("monthly_breakdown", {})

    engine_breakdown = []
    for engine_key, display_name in engine_names.items():
        count = breakdown.get(engine_key, 0)
        amount = abs(float(monthly_breakdown.get(engine_key, 0.0)))
        engine_breakdown.append({
            "name": display_name,
            "amount": round(amount, 2),
            "confidence": 0.85,
            "count": count,
        })

    return {
        "total_overcharges": round(total_monthly, 2),
        "annualized_savings": round(total_annualised, 2),
        "total_flags": total_flags,
        "status": "Complete" if audit.status == AuditStatus.complete else audit.status.value.capitalize() if audit.status else "Unknown",
        "engine_breakdown": sorted(engine_breakdown, key=lambda x: x["amount"], reverse=True),
        "client_name": client.company_name,
        "client_id": str(client.id),
        "output_files": raw.get("output_files", {}),
    }


@router.get("/{client_id}/dashboard")
async def get_dashboard_data(
    client: Client = Depends(get_client_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Return data formatted for the dashboard frontend."""
    result = await db.execute(
        select(AuditResult)
        .where(AuditResult.client_id == client.id)
        .order_by(AuditResult.created_at.desc())
        .limit(1)
    )
    audit = result.scalar_one_or_none()

    if not audit or audit.status != AuditStatus.complete:
        return {
            "status": "ok",
            "client_id": str(client.id),
            "client_name": client.company_name,
            "total_overcharges": 0,
            "annualized_savings": 0,
            "total_flags": 0,
            "status": "No audit data",
            "chart_data": [],
            "engine_breakdown": [],
            "flags": [],
        }

    dashboard = _extract_dashboard_data(audit, client)
    dashboard["status"] = "ok"
    dashboard["client_id"] = str(client.id)
    return dashboard


# ── GET /api/client/{client_id}/download-report ────────────────────


@router.get("/{client_id}/download-report")
async def download_report(
    client: Client = Depends(get_client_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Generate and download an Excel dispute schedule report."""
    result = await db.execute(
        select(AuditResult)
        .where(AuditResult.client_id == client.id)
        .order_by(AuditResult.created_at.desc())
        .limit(1)
    )
    audit = result.scalar_one_or_none()

    if not audit:
        raise HTTPException(status_code=404, detail="No audit results found. Run an audit first.")

    raw = audit.raw_results_json or {}
    output_files = raw.get("output_files", {})
    excel_path = output_files.get("excel_schedule")

    if not excel_path or not Path(excel_path).exists():
        # Try per-client output directory
        client_output_dir = OUTPUT_DIR / str(client.id)
        if client_output_dir.exists():
            existing = sorted(client_output_dir.glob("Dispute_Schedule_*.xlsx"))
            if existing:
                excel_path = str(existing[-1])

    if not excel_path or not Path(excel_path).exists():
        raise HTTPException(status_code=404, detail="Report file not found. Re-run the audit.")

    filename = Path(excel_path).name
    return FileResponse(
        path=excel_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ── GET /api/client/{client_id}/documents ─────────────────────────


@router.get("/{client_id}/documents")
async def list_documents(
    client: Client = Depends(get_client_or_404),
    db: AsyncSession = Depends(get_db),
):
    """List all generated documents for a client: dispute schedule, letter, executive summary."""
    result = await db.execute(
        select(AuditResult)
        .where(AuditResult.client_id == client.id)
        .order_by(AuditResult.created_at.desc())
        .limit(1)
    )
    audit = result.scalar_one_or_none()

    if not audit:
        raise HTTPException(status_code=404, detail="No audit results found.")

    raw = audit.raw_results_json or {}
    output_files = raw.get("output_files", {})

    client_output_dir = OUTPUT_DIR / str(client.id)

    documents = []

    # Dispute schedule (Excel)
    excel_path = output_files.get("excel_schedule")
    if not excel_path or not Path(excel_path).exists():
        if client_output_dir.exists():
            existing = sorted(client_output_dir.glob("Dispute_Schedule_*.xlsx"))
            if existing:
                excel_path = str(existing[-1])

    if excel_path and Path(excel_path).exists():
        p = Path(excel_path)
        documents.append({
            "type": "dispute_schedule",
            "format": "xlsx",
            "filename": p.name,
            "file_size": p.stat().st_size,
            "download_url": f"/api/client/{client.id}/download-report",
        })

    # Dispute letter (text)
    letter_path = output_files.get("dispute_letter")
    if letter_path and Path(letter_path).exists():
        p = Path(letter_path)
        content = p.read_text(encoding="utf-8")
        documents.append({
            "type": "dispute_letter",
            "format": "txt",
            "filename": p.name,
            "file_size": p.stat().st_size,
            "content": content,
            "download_url": None,
        })
    elif client_output_dir.exists():
        existing = sorted(client_output_dir.glob("Dispute_Letter_*.txt"))
        if existing:
            p = existing[-1]
            content = p.read_text(encoding="utf-8")
            documents.append({
                "type": "dispute_letter",
                "format": "txt",
                "filename": p.name,
                "file_size": p.stat().st_size,
                "content": content,
                "download_url": None,
            })

    # Executive summary (markdown)
    summary_path = output_files.get("executive_summary")
    if summary_path and Path(summary_path).exists():
        p = Path(summary_path)
        content = p.read_text(encoding="utf-8")
        documents.append({
            "type": "executive_summary",
            "format": "md",
            "filename": p.name,
            "file_size": p.stat().st_size,
            "content": content,
            "download_url": None,
        })
    elif client_output_dir.exists():
        existing = sorted(client_output_dir.glob("Executive_Summary_*.md"))
        if existing:
            p = existing[-1]
            content = p.read_text(encoding="utf-8")
            documents.append({
                "type": "executive_summary",
                "format": "md",
                "filename": p.name,
                "file_size": p.stat().st_size,
                "content": content,
                "download_url": None,
            })

    return {
        "status": "ok",
        "client_id": str(client.id),
        "client_name": client.company_name,
        "documents": documents,
    }


# ── GET /api/client/{client_id}/status ─────────────────────────────


@router.get("/{client_id}/status")
async def get_client_status(
    client: Client = Depends(get_client_or_404),
):
    """Return the current status of a client."""
    return {
        "status": "ok",
        "client_id": str(client.id),
        "company_name": client.company_name,
        "client_status": client.status.value if client.status else None,
        "authorized": client.status in (ClientStatus.authorized, ClientStatus.files_uploaded,
                                         ClientStatus.audit_running, ClientStatus.audit_complete,
                                         ClientStatus.dispute_submitted, ClientStatus.settled),
    }
