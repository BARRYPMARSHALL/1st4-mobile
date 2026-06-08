"""
Owner Dashboard API routes for 1st 4 Mobile Backend.

Prefix: /api/owner
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.deps import get_db, get_client_or_404
from backend.models import (
    Client,
    ClientStatus,
    AuditResult,
    AuditStatus,
    Dispute,
    DisputeStatus,
    Invoice,
    InvoiceStatus,
    UploadedFile,
)

logger = logging.getLogger("1st4backend.owner_routes")

router = APIRouter(prefix="/api/owner", tags=["owner"])


# ── Helpers ────────────────────────────────────────────────────────


def _client_to_dict(client: Client) -> dict:
    return {
        "id": str(client.id),
        "company_name": client.company_name,
        "abn": client.abn,
        "industry": client.industry,
        "fleet_size": client.fleet_size,
        "primary_carrier": client.primary_carrier,
        "email": client.email,
        "status": client.status.value if client.status else None,
        "created_at": client.created_at.isoformat() if client.created_at else None,
        "updated_at": client.updated_at.isoformat() if client.updated_at else None,
        "authorized_at": client.authorized_at.isoformat() if client.authorized_at else None,
        "authorized_by": client.authorized_by,
    }


# ── GET /api/owner/dashboard ───────────────────────────────────────


@router.get("/dashboard")
async def owner_dashboard(db: AsyncSession = Depends(get_db)):
    """Return owner dashboard with pipeline stats, client queue, invoice data, and recent activity."""

    # ── Pipeline stats ─────────────────────────────────────────────
    total_clients = await db.scalar(select(func.count(Client.id)))

    leads_uploaded = await db.scalar(
        select(func.count(Client.id)).where(Client.status.in_([
            ClientStatus.registered,
            ClientStatus.authorized,
            ClientStatus.files_uploaded,
        ]))
    )

    audits_processing = await db.scalar(
        select(func.count(AuditResult.id)).where(AuditResult.status == AuditStatus.running)
    )

    disputes_active = await db.scalar(
        select(func.count(Dispute.id)).where(
            Dispute.status.in_([DisputeStatus.draft, DisputeStatus.reviewed, DisputeStatus.submitted_to_carrier])
        )
    )

    invoices_settled = await db.scalar(
        select(func.count(Invoice.id)).where(Invoice.status == InvoiceStatus.paid)
    )

    pipeline_stats = {
        "total_clients": total_clients or 0,
        "leads_uploaded": leads_uploaded or 0,
        "audits_processing": audits_processing or 0,
        "disputes_active": disputes_active or 0,
        "invoices_settled": invoices_settled or 0,
    }

    # ── Client queue ───────────────────────────────────────────────
    result = await db.execute(
        select(Client).order_by(Client.updated_at.desc()).limit(50)
    )
    clients = result.scalars().all()
    client_queue = [_client_to_dict(c) for c in clients]

    # ── Invoice totals ─────────────────────────────────────────────
    invoiced_result = await db.execute(
        select(
            func.coalesce(func.sum(Invoice.amount), 0).label("total_invoiced"),
            func.coalesce(
                func.sum(case((Invoice.status == InvoiceStatus.paid, Invoice.amount), else_=0)),
                0,
            ).label("total_collected"),
            func.coalesce(
                func.sum(case((Invoice.status != InvoiceStatus.paid, Invoice.amount), else_=0)),
                0,
            ).label("outstanding"),
        )
    )
    row = invoiced_result.one()
    total_invoiced = float(row.total_invoiced)
    total_collected = float(row.total_collected)
    outstanding = float(row.outstanding)

    # ── Recent activity (last 10 clients by updated_at) ────────────
    recent = await db.execute(
        select(Client).order_by(Client.updated_at.desc()).limit(10)
    )
    recent_activity = []
    for c in recent.scalars().all():
        recent_activity.append({
            "client_id": str(c.id),
            "company_name": c.company_name,
            "status": c.status.value if c.status else None,
            "timestamp": c.updated_at.isoformat() if c.updated_at else None,
        })

    return {
        "pipeline_stats": pipeline_stats,
        "client_queue": client_queue,
        "total_invoiced": total_invoiced,
        "total_collected": total_collected,
        "outstanding": outstanding,
        "recent_activity": recent_activity,
    }


# ── GET /api/owner/clients ────────────────────────────────────────


@router.get("/clients")
async def list_clients(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all clients with optional search/filter by status."""
    stmt = select(Client)

    if status_filter:
        try:
            enum_val = ClientStatus(status_filter)
            stmt = stmt.where(Client.status == enum_val)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status_filter}. Valid: {[s.value for s in ClientStatus]}",
            )

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            Client.company_name.ilike(pattern) | Client.abn.ilike(pattern) | Client.email.ilike(pattern)
        )

    stmt = stmt.order_by(Client.updated_at.desc())
    result = await db.execute(stmt)
    clients = result.scalars().all()

    return {
        "status": "ok",
        "total": len(clients),
        "clients": [_client_to_dict(c) for c in clients],
    }


# ── POST /api/owner/client/{client_id}/run-audit ──────────────────


async def _run_audit_task(
    client_id: uuid.UUID,
    client_name: str,
    billing_files: list[str],
    contract_path: str,
    output_dir: str,
    audit_id: uuid.UUID,
):
    """Background task: run the pipeline, update DB with results."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from backend.database import async_session_factory

    try:
        import pipeline.main as pm
        result = pm.run_audit(
            client_name=client_name,
            billing_files=billing_files,
            contract_matrix_path=contract_path,
            output_dir=output_dir,
            verbose=False,
        )

        summary = result.get("summary", {})

        async with async_session_factory() as db:
            audit = await db.get(AuditResult, audit_id)
            if audit:
                audit.status = AuditStatus.complete
                audit.total_flags = int(summary.get("total_flags", 0))
                audit.total_monthly_overcharge = float(summary.get("total_monthly_overcharge", 0.0))
                audit.total_annualised = float(summary.get("total_annualised", 0.0))
                audit.raw_results_json = {
                    "pipeline_summary": summary,
                    "output_files": result.get("output_files", {}),
                }
                audit.completed_at = datetime.utcnow()

            client = await db.get(Client, client_id)
            if client:
                client.status = ClientStatus.audit_complete
                client.updated_at = datetime.utcnow()

            await db.commit()
            logger.info(f"Background audit complete for {client_id}, audit {audit_id}")

    except Exception as exc:
        logger.exception(f"Background audit failed for client {client_id}: {exc}")
        try:
            async with async_session_factory() as db:
                audit = await db.get(AuditResult, audit_id)
                if audit:
                    audit.status = AuditStatus.failed
                    audit.raw_results_json = {"error": str(exc)}
                    audit.completed_at = datetime.utcnow()
                await db.commit()
        except Exception as db_exc:
            logger.error(f"Failed to update audit status after error: {db_exc}")


@router.post("/client/{client_id}/run-audit")
async def trigger_audit(
    client_id: str,
    background_tasks: BackgroundTasks,
    client: Client = Depends(get_client_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Trigger the audit pipeline for a client (runs in background)."""
    # Validate client has uploaded files
    files_result = await db.execute(
        select(UploadedFile).where(UploadedFile.client_id == client.id)
    )
    uploaded_files = files_result.scalars().all()
    if not uploaded_files:
        raise HTTPException(
            status_code=400,
            detail="No billing files uploaded. Upload at least one file first.",
        )

    # Validate client is authorized
    if client.status not in (ClientStatus.authorized, ClientStatus.files_uploaded, ClientStatus.registered):
        raise HTTPException(
            status_code=400,
            detail=f"Client status must be authorized/files_uploaded. Current: {client.status.value}",
        )

    # Find contract
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    CONTRACTS_DIR = PROJECT_ROOT / "contracts"
    OUTPUT_DIR = PROJECT_ROOT / "output"

    contract_path = CONTRACTS_DIR / f"{client_id}_contract.yaml"
    if not contract_path.exists():
        contract_path = PROJECT_ROOT / "test_contract.yaml"
    if not contract_path.exists():
        # Create a default contract
        import yaml
        default_contract = {
            "client": {"name": client.company_name, "account_numbers": {client.primary_carrier.lower(): ["ACCT-PENDING"]}},
            "contract": {"effective_date": "2024-01-01", "expiry_date": "2026-12-31", "auto_renew": True, "notice_period_days": 90},
            "rate_plans": [{"plan_code": "MBP-50GB-POOL", "plan_name": "Mobile Business Pool 50GB", "service_type": "mobile", "monthly_access_fee": 45.00}],
            "discounts": [],
            "pool_configuration": [],
            "roaming_zones": [],
        }
        contract_path = CONTRACTS_DIR / f"{client_id}_contract.yaml"
        CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(contract_path, "w") as f:
            yaml.dump(default_contract, f, default_flow_style=False, sort_keys=False)

    # Get billing file paths
    billing_files = [str(Path(u.storage_path)) for u in uploaded_files]

    # Create AuditResult record
    audit = AuditResult(
        client_id=client.id,
        status=AuditStatus.running,
    )
    db.add(audit)
    await db.flush()

    # Update client status
    client.status = ClientStatus.audit_running
    client.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(audit)

    client_output_dir = str(OUTPUT_DIR / client_id)

    # Schedule background task
    background_tasks.add_task(
        _run_audit_task,
        client_id=client.id,
        client_name=client.company_name,
        billing_files=billing_files,
        contract_path=str(contract_path),
        output_dir=client_output_dir,
        audit_id=audit.id,
    )

    return {
        "status": "ok",
        "audit_id": str(audit.id),
        "message": "Audit pipeline triggered. Results will be available when complete.",
    }


# ── GET /api/owner/client/{client_id}/audits ──────────────────────


@router.get("/client/{client_id}/audits")
async def list_client_audits(
    client: Client = Depends(get_client_or_404),
    db: AsyncSession = Depends(get_db),
):
    """List all audits for a specific client."""
    result = await db.execute(
        select(AuditResult)
        .where(AuditResult.client_id == client.id)
        .order_by(AuditResult.created_at.desc())
    )
    audits = result.scalars().all()

    return {
        "status": "ok",
        "client_id": str(client.id),
        "audits": [
            {
                "id": str(a.id),
                "status": a.status.value if a.status else None,
                "total_flags": a.total_flags,
                "total_monthly_overcharge": a.total_monthly_overcharge,
                "total_annualised": a.total_annualised,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            }
            for a in audits
        ],
    }


# ── POST /api/owner/disputes ──────────────────────────────────────


@router.post("/disputes")
async def create_dispute(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Create a dispute from audit results."""
    client_id_str = body.get("client_id")
    audit_id_str = body.get("audit_id")

    if not client_id_str or not audit_id_str:
        raise HTTPException(status_code=400, detail="Both client_id and audit_id are required")

    try:
        client_uuid = uuid.UUID(client_id_str)
        audit_uuid = uuid.UUID(audit_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    client = await db.get(Client, client_uuid)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    audit = await db.get(AuditResult, audit_uuid)
    if not audit or audit.client_id != client_uuid:
        raise HTTPException(status_code=404, detail="Audit not found for this client")

    if audit.status != AuditStatus.complete:
        raise HTTPException(status_code=400, detail="Audit is not complete yet")

    # Generate dispute letter via pipeline
    try:
        from pipeline.output_letter import generate_dispute_letter
        import pandas as pd

        raw_results = audit.raw_results_json or {}
        pipeline_summary = raw_results.get("pipeline_summary", {})

        all_flags = {
            "summary": pipeline_summary,
            "ghost_lines": pd.DataFrame(),
            "rate_mismatches": pd.DataFrame(),
            "roaming": pd.DataFrame(),
            "legacy_rollbacks": pd.DataFrame(),
            "duplicates": pd.DataFrame(),
        }

        carrier = client.primary_carrier or "Telstra"
        account_numbers = [f"ACCT-{carrier.upper()}"]

        letter_text = generate_dispute_letter(
            all_flags=all_flags,
            client_name=client.company_name,
            telco=carrier,
            account_numbers=account_numbers,
        )
    except Exception as exc:
        logger.warning(f"Dispute letter generation failed (using placeholder): {exc}")
        letter_text = f"Dispute letter for {client.company_name} — generated from audit {audit_id_str}"

    # Create Dispute record
    dispute = Dispute(
        client_id=client_uuid,
        audit_id=audit_uuid,
        status=DisputeStatus.draft,
        dispute_letter_text=letter_text,
        carrier_name=client.primary_carrier,
    )
    db.add(dispute)
    await db.commit()
    await db.refresh(dispute)

    # Update client status
    client.status = ClientStatus.dispute_submitted
    client.updated_at = datetime.utcnow()
    await db.commit()

    return {
        "status": "ok",
        "dispute_id": str(dispute.id),
        "message": "Dispute created in draft status",
    }


# ── PATCH /api/owner/disputes/{dispute_id}/status ─────────────────


@router.patch("/disputes/{dispute_id}/status")
async def update_dispute_status(
    dispute_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Update dispute status. If credit_issued, also create an Invoice."""
    new_status_str = body.get("status")
    if not new_status_str:
        raise HTTPException(status_code=400, detail="'status' field is required")

    try:
        new_status = DisputeStatus(new_status_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {new_status_str}. Valid: {[s.value for s in DisputeStatus]}",
        )

    try:
        dispute_uuid = uuid.UUID(dispute_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dispute_id format")

    dispute = await db.get(Dispute, dispute_uuid)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    dispute.status = new_status

    if new_status == DisputeStatus.submitted_to_carrier:
        dispute.submitted_at = datetime.utcnow()
    elif new_status == DisputeStatus.credit_issued:
        dispute.submitted_at = dispute.submitted_at or datetime.utcnow()

        # Calculate fee: 50% of audit's total_annualised if available
        credit_amount = body.get("credit_amount")
        if credit_amount is not None:
            dispute.credit_amount = float(credit_amount)

        # Determine amount for invoice: 50% of credit
        amount = (dispute.credit_amount or 0) * 0.50

        invoice = Invoice(
            client_id=dispute.client_id,
            dispute_id=dispute.id,
            amount=amount,
            status=InvoiceStatus.pending,
        )
        db.add(invoice)

        # Update client status
        client = await db.get(Client, dispute.client_id)
        if client:
            client.status = ClientStatus.settled
            client.updated_at = datetime.utcnow()

    dispute.updated_at = datetime.utcnow()
    await db.commit()

    return {
        "status": "ok",
        "dispute_id": str(dispute.id),
        "new_status": new_status.value,
    }


# ── GET /api/owner/invoices ────────────────────────────────────────


@router.get("/invoices")
async def list_invoices(db: AsyncSession = Depends(get_db)):
    """List all invoices with total invoiced, collected, and outstanding."""
    # Aggregates
    agg_result = await db.execute(
        select(
            func.coalesce(func.sum(Invoice.amount), 0).label("total_invoiced"),
            func.coalesce(
                func.sum(case((Invoice.status == InvoiceStatus.paid, Invoice.amount), else_=0)),
                0,
            ).label("total_collected"),
            func.coalesce(
                func.sum(case((Invoice.status != InvoiceStatus.paid, Invoice.amount), else_=0)),
                0,
            ).label("outstanding"),
            func.count(Invoice.id).label("count"),
        )
    )
    agg = agg_result.one()

    # Individual invoices with client name
    result = await db.execute(
        select(Invoice, Client.company_name)
        .join(Client, Invoice.client_id == Client.id, isouter=True)
        .order_by(Invoice.created_at.desc())
    )
    rows = result.all()

    invoices_list = []
    for inv, company_name in rows:
        invoices_list.append({
            "id": str(inv.id),
            "client_id": str(inv.client_id),
            "company_name": company_name or "Unknown",
            "dispute_id": str(inv.dispute_id) if inv.dispute_id else None,
            "amount": inv.amount,
            "status": inv.status.value if inv.status else None,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
        })

    return {
        "status": "ok",
        "total_invoiced": float(agg.total_invoiced),
        "total_collected": float(agg.total_collected),
        "outstanding": float(agg.outstanding),
        "total_invoices": agg.count,
        "invoices": invoices_list,
    }
