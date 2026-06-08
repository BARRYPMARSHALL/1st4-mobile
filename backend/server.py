"""
1st 4 Mobile — FastAPI Backend Server

Serves the www/ static frontend and exposes REST APIs for:
  - Client registration and authorisation
  - File upload (CSV, PDF, XLSX)
  - Audit pipeline execution
  - Audit results and dashboard data
  - Excel report download
"""

import base64
import json
import logging
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ── Project paths ─────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WWW_DIR = PROJECT_ROOT / "www"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_DIR = Path(__file__).resolve().parent / "data"

# ── Backend-local imports ─────────────────────────────────────────
from backend.loa_template import get_loa_text
from backend.client_store import (
    create_client,
    get_client,
    save_authorization,
    get_results,
    save_results,
    list_uploads,
    update_client,
)

# ── Logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
logger = logging.getLogger("1st4backend.server")

# ── Ensure required directories ────────────────────────────────────
for d in [WWW_DIR, UPLOADS_DIR, CONTRACTS_DIR, OUTPUT_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════════════════════
# App Initialisation
# ══════════════════════════════════════════════════════════════════

app = FastAPI(
    title="1st 4 Mobile Billing Audit API",
    version="1.0.0",
    docs_url="/docs",
)

# ── CORS ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static file serving ────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(WWW_DIR)), name="www_static")


# ══════════════════════════════════════════════════════════════════
# Helper Utilities
# ══════════════════════════════════════════════════════════════════

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


def _load_pipeline():
    """Lazy-import the pipeline modules (avoids early import errors)."""
    import pipeline.main as pm
    import pipeline.detect_runner as dr
    return pm, dr


def _create_default_contract(client_id: str, company_name: str, carrier: str) -> str:
    """Create a boilerplate contract YAML for a client based on carrier."""
    default_contract = {
        "client": {
            "name": company_name,
            "account_numbers": {
                "telstra": [] if carrier.lower() != "telstra" else ["ACCT-PENDING"],
                "optus": [] if carrier.lower() != "optus" else ["ACCT-PENDING"],
            },
        },
        "contract": {
            "effective_date": "2024-01-01",
            "expiry_date": "2026-12-31",
            "auto_renew": True,
            "notice_period_days": 90,
        },
        "rate_plans": [
            {
                "plan_code": "MBP-50GB-POOL",
                "plan_name": "Mobile Business Pool 50GB",
                "service_type": "mobile",
                "monthly_access_fee": 45.00,
                "data_pool": {"included": 51200, "overage_rate": 0.002},
                "voice": "unlimited_national",
                "sms": "unlimited",
                "contract_term_months": 24,
            },
            {
                "plan_code": "MBP-200GB-POOL",
                "plan_name": "Mobile Business Pool 200GB",
                "service_type": "mobile",
                "monthly_access_fee": 85.00,
                "data_pool": {"included": 204800, "overage_rate": 0.0015},
                "voice": "unlimited_national",
                "sms": "unlimited",
                "contract_term_months": 24,
            },
        ],
        "discounts": [
            {
                "name": "Standard Volume Discount",
                "type": "percentage",
                "value": 10.0,
                "applies_to": ["*"],
                "condition": "total_sims >= 100",
            }
        ],
        "pool_configuration": [],
        "roaming_zones": [
            {
                "zone": "Zone 1 (NZ, US, UK, Canada)",
                "data_rate": 0.00,
                "voice_rate": 0.50,
                "sms_rate": 0.00,
            },
            {
                "zone": "Zone 2 (Asia)",
                "data_rate": 0.01,
                "voice_rate": 1.00,
                "sms_rate": 0.50,
            },
            {
                "zone": "Zone 3 (Rest of World)",
                "data_rate": 0.02,
                "voice_rate": 2.50,
                "sms_rate": 1.00,
            },
        ],
    }

    contract_path = CONTRACTS_DIR / f"{client_id}_contract.yaml"
    with open(contract_path, "w") as f:
        yaml.dump(default_contract, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Created default contract for {client_id} at {contract_path}")
    return str(contract_path)


def _find_contract(client_id: str) -> Optional[str]:
    """Find an existing contract YAML for a client, or return None."""
    # Look for client-specific contract
    contract_path = CONTRACTS_DIR / f"{client_id}_contract.yaml"
    if contract_path.exists():
        return str(contract_path)

    # Fall back to the project test contract
    test_contract = PROJECT_ROOT / "test_contract.yaml"
    if test_contract.exists():
        return str(test_contract)

    return None


def _extract_dashboard_data(results: dict, client: dict) -> dict:
    """Transform raw audit results into dashboard-friendly format."""
    summary = results.get("summary", results.get("pipeline_summary", {}))
    if not summary:
        # Try older format
        summary = results.get("results", {}).get("summary", results)

    total_monthly = float(summary.get("total_monthly_overcharge", 0.0))
    total_annualised = float(summary.get("total_annualised", total_monthly * 12))
    total_flags = int(summary.get("total_flags", 0))

    breakdown = summary.get("breakdown", {})
    if isinstance(breakdown, dict):
        keys = list(breakdown.keys())
    else:
        keys = ["ghost_lines", "rate_mismatches", "roaming", "legacy_rollbacks", "duplicates"]
        breakdown = {k: 0 for k in keys}

    monthly_breakdown = summary.get("monthly_breakdown", {})
    engine_names = {
        "ghost_lines": "Ghost Lines",
        "rate_mismatches": "Rate Mismatches",
        "roaming": "Roaming Anomalies",
        "legacy_rollbacks": "Legacy Rollbacks",
        "duplicates": "Duplicate Services",
    }

    # Engine breakdown for dashboard chart
    engine_breakdown = []
    for engine_key, display_name in engine_names.items():
        count = breakdown.get(engine_key, 0)
        if count == 0 and engine_key not in monthly_breakdown:
            continue  # skip zero-count engines if amount is also zero
        amount = abs(float(monthly_breakdown.get(engine_key, 0.0)))
        confidence = 0.85  # default confidence; real value would come from engine metadata
        engine_breakdown.append({
            "name": display_name,
            "amount": round(amount, 2),
            "confidence": confidence,
            "count": count,
        })

    # Build monthly drift array (mock if real data not available)
    from datetime import datetime, timedelta
    chart_data = []
    for m in range(12):
        month_date = (datetime.utcnow().replace(day=1) - timedelta(days=30 * m)).strftime(
            "%Y-%m"
        )
        chart_data.append({
            "month": month_date,
            "overcharge": round(total_monthly / max(len(monthly_breakdown), 1), 2),
        })
    chart_data.reverse()  # chronological order

    # Build flags list for the table ledger
    flags = []
    for engine_key, display_name in engine_names.items():
        engine_df_key = engine_key  # e.g., 'ghost_lines', 'rate_mismatches'
        engine_flags_raw = results.get(engine_df_key)
        if engine_flags_raw is not None and isinstance(engine_flags_raw, list):
            for flag in engine_flags_raw:
                flags.append({
                    "engine": display_name,
                    "service_id": flag.get("service_id", flag.get("service_number", "Unknown")),
                    "description": flag.get("detail", flag.get("description", "")),
                    "amount": float(flag.get("estimated_monthly_overcharge", flag.get("variance_amount", flag.get("charge_amount", 0)))),
                    "confidence": flag.get("confidence", 0.85),
                    "status": "Flagged",
                })

    # Try to extract from the output files list too
    output_files = results.get("output_files", {})

    return {
        "total_overcharges": round(total_monthly, 2),
        "annualized_savings": round(total_annualised, 2),
        "total_flags": total_flags,
        "status": "Complete" if client.get("authorized") else "Awaiting Authorization",
        "chart_data": chart_data,
        "engine_breakdown": sorted(engine_breakdown, key=lambda x: x["amount"], reverse=True),
        "flags": sorted(flags, key=lambda x: x["amount"], reverse=True),
        "client_name": client.get("company_name", ""),
        "client_id": client.get("client_id", ""),
        "output_files": output_files,
    }


def _generate_excel_report(client_id: str) -> Optional[str]:
    """Return an existing Excel dispute schedule or regenerate from cached results.

    Priority:
      1. Check the output file path from the last audit run (from cached results).
      2. Check the per-client output directory for any Excel file.
      3. Attempt regeneration from cached summary data.
    """
    client = get_client(client_id)
    if not client:
        return None
    results = get_results(client_id)
    if not results:
        return None

    # 1. Check the path from the previous pipeline run
    output_files = results.get("output_files", {})
    excel_path = output_files.get("excel_schedule")
    if excel_path and Path(excel_path).exists():
        return excel_path

    # 2. Check per-client output directory
    client_output_dir = OUTPUT_DIR / client_id
    if client_output_dir.exists():
        existing = sorted(client_output_dir.glob("Dispute_Schedule_*.xlsx"))
        if existing:
            return str(existing[-1])

    # 3. Attempt regeneration from summary data
    try:
        import pandas as pd
        from pipeline.output_excel import generate_dispute_schedule

        # Build minimal all_flags from cached summary
        summary = results.get("pipeline_summary", results.get("summary", {}))
        all_flags = {
            "ghost_lines": pd.DataFrame(),
            "rate_mismatches": pd.DataFrame(),
            "roaming": pd.DataFrame(),
            "legacy_rollbacks": pd.DataFrame(),
            "duplicates": pd.DataFrame(),
            "summary": summary,
        }

        company_name = client.get("company_name", client_id).replace(" ", "_")
        out_path = str(client_output_dir / f"Dispute_Schedule_{company_name}.xlsx")
        client_output_dir.mkdir(parents=True, exist_ok=True)

        excel_path = generate_dispute_schedule(
            all_flags=all_flags,
            df_raw=pd.DataFrame(),
            client_name=client.get("company_name", client_id),
            output_path=out_path,
        )
        return excel_path
    except Exception as exc:
        logger.error(f"Excel regeneration failed for {client_id}: {exc}")
        return None


def _serve_html(filename: str, request: Request) -> HTMLResponse:
    """Serve an HTML file from the www/ directory."""
    path = WWW_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found")
    content = path.read_text(encoding="utf-8")
    return HTMLResponse(content=content)


# ══════════════════════════════════════════════════════════════════
# Routes — Frontend Pages
# ══════════════════════════════════════════════════════════════════


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request):
    return _serve_html("index.html", request)


@app.get("/portal", response_class=HTMLResponse, include_in_schema=False)
async def portal(request: Request):
    return _serve_html("portal.html", request)


@app.get("/dashboard/{client_id}", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(client_id: str, request: Request):
    return _serve_html("dashboard.html", request)


# ══════════════════════════════════════════════════════════════════
# API Routes — File Upload
# ══════════════════════════════════════════════════════════════════


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), client_id: str = Form(...)):
    """Upload a billing file for a client.

    Accepts .csv, .pdf, .xlsx files up to 200 MB.
    Saves to uploads/{client_id}/{filename}.
    """
    # Validate client exists
    client = get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    # Validate file
    _validate_file(file)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of 200 MB",
        )

    # Save
    file_id = str(uuid.uuid4())
    client_dir = UPLOADS_DIR / client_id
    client_dir.mkdir(parents=True, exist_ok=True)
    dest = client_dir / (file.filename or f"upload_{file_id}")
    with open(dest, "wb") as f:
        f.write(content)

    logger.info(f"Uploaded {file.filename} ({len(content)} bytes) for client {client_id} → {dest}")
    return {
        "status": "ok",
        "file_id": file_id,
        "filename": file.filename,
        "size_bytes": len(content),
    }


# ══════════════════════════════════════════════════════════════════
# API Routes — Client Registration
# ══════════════════════════════════════════════════════════════════


class ClientRegistrationRequest:
    """Expected JSON body for client registration."""
    def __init__(
        self,
        company_name: str = "",
        abn: str = "",
        industry: str = "",
        fleet_size: int = 0,
        primary_carrier: str = "Telstra",
        email: str = "",
    ):
        self.company_name = company_name
        self.abn = abn
        self.industry = industry
        self.fleet_size = fleet_size
        self.primary_carrier = primary_carrier
        self.email = email


@app.post("/api/client/register")
async def register_client(request: Request):
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

    client_id = create_client(data)
    carrier = data.get("primary_carrier", "Telstra")

    loa_text = get_loa_text(
        company_name=data["company_name"],
        abn=data["abn"],
        carrier=carrier,
    )

    logger.info(f"Registered client {client_id}: {data['company_name']} ({carrier})")
    return {
        "status": "ok",
        "client_id": client_id,
        "loa_text": loa_text,
    }


# ══════════════════════════════════════════════════════════════════
# API Routes — Client Authorisation
# ══════════════════════════════════════════════════════════════════


@app.post("/api/client/{client_id}/authorize")
async def authorize_client(client_id: str, request: Request):
    """Authorise 1st 4 Mobile to act on behalf of a client.

    Accepts a base64-encoded PNG signature and the signatory name.
    Saves the signature and creates a boilerplate contract.
    """
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

    success = save_authorization(client_id, signature_data, signed_by)
    if not success:
        raise HTTPException(status_code=400, detail=f"Authorization failed for client {client_id}. Check signature data and try again.")

    # Create a default contract if one doesn't already exist
    client = get_client(client_id)
    contract_path = CONTRACTS_DIR / f"{client_id}_contract.yaml"
    if not contract_path.exists() and client:
        _create_default_contract(
            client_id=client_id,
            company_name=client.get("company_name", "Unknown"),
            carrier=client.get("primary_carrier", "Telstra"),
        )

    logger.info(f"Client {client_id} authorized by {signed_by}")
    return {
        "status": "ok",
        "authorized": True,
        "signed_by": signed_by,
    }


# ══════════════════════════════════════════════════════════════════
# API Routes — Pipeline Execution
# ══════════════════════════════════════════════════════════════════


@app.post("/api/client/{client_id}/run-audit")
async def run_audit(client_id: str):
    """Execute the billing audit pipeline for a client.

    Scans uploads/{client_id}/ for billing files, loads the
    contract matrix, runs all detection engines, caches results.
    """
    client = get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    if not client.get("authorized"):
        raise HTTPException(
            status_code=400,
            detail="Client must be authorised before running an audit",
        )

    # Find billing files
    billing_files = list_uploads(client_id)
    if not billing_files:
        raise HTTPException(
            status_code=400,
            detail="No billing files uploaded. Upload at least one CSV, PDF, or XLSX file first.",
        )

    # Find or create contract
    contract_path = _find_contract(client_id)
    if not contract_path:
        contract_path = _create_default_contract(
            client_id=client_id,
            company_name=client.get("company_name", "Unknown"),
            carrier=client.get("primary_carrier", "Telstra"),
        )

    # Run audit
    try:
        pm, _ = _load_pipeline()
        import pipeline.config as cfg

        client_output_dir = str(OUTPUT_DIR / client_id)
        logger.info(
            f"Running audit for {client_id}: {len(billing_files)} files, "
            f"contract={contract_path}"
        )

        result = pm.run_audit(
            client_name=client.get("company_name", client_id),
            billing_files=billing_files,
            contract_matrix_path=contract_path,
            output_dir=client_output_dir,
            verbose=False,
        )

        # Save results with summary as JSON-serialisable dict
        # Convert DataFrames in all_flags-like data to lists
        cache_entry = {
            "pipeline_summary": result.get("summary", {}),
            "output_files": result.get("output_files", {}),
            "audit_log": result.get("audit_log", ""),
        }

        # Try to extract full detection data from results
        # The run_audit result dict has summary, output_files, audit_log
        # The actual flag DataFrames are returned inside the detection runner
        # but not directly from run_audit. We supplement with the key numbers.
        save_results(client_id, cache_entry)

        summary = result.get("summary", {})
        logger.info(
            f"Audit complete for {client_id}: "
            f"{summary.get('total_flags', 0)} flags, "
            f"${summary.get('total_monthly_overcharge', 0):.2f}/month"
        )

        return {
            "status": "ok",
            "results": {
                "total_flags": summary.get("total_flags", 0),
                "total_monthly_overcharge": summary.get("total_monthly_overcharge", 0),
                "total_annualised": summary.get("total_annualised", 0),
                "breakdown": summary.get("breakdown", {}),
                "monthly_breakdown": summary.get("monthly_breakdown", {}),
                "output_files": result.get("output_files", {}),
            },
        }

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception(f"Audit pipeline failed for {client_id}")
        raise HTTPException(status_code=500, detail=f"Audit pipeline error: {exc}")


# ══════════════════════════════════════════════════════════════════
# API Routes — Results
# ══════════════════════════════════════════════════════════════════


@app.get("/api/client/{client_id}/results")
async def get_results_api(client_id: str):
    """Return the cached audit results for a client."""
    client = get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    results = get_results(client_id)
    if not results:
        raise HTTPException(
            status_code=404,
            detail="No audit results found. Run an audit first via POST /api/client/{client_id}/run-audit",
        )

    return {
        "status": "ok",
        "client_id": client_id,
        "client_name": client.get("company_name", ""),
        "results": results,
    }


@app.get("/api/client/{client_id}/dashboard")
async def get_dashboard_data(client_id: str):
    """Return data formatted for the dashboard frontend."""
    client = get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    results = get_results(client_id)
    if not results:
        # Return a "no data yet" dashboard skeleton
        return {
            "status": "ok",
            "client_id": client_id,
            "client_name": client.get("company_name", ""),
            "total_overcharges": 0,
            "annualized_savings": 0,
            "total_flags": 0,
            "status": "No audit data",
            "chart_data": [],
            "engine_breakdown": [],
            "flags": [],
        }

    dashboard = _extract_dashboard_data(results, client)
    dashboard["status"] = "ok"
    dashboard["client_id"] = client_id
    return dashboard


@app.get("/api/client/{client_id}/download-report")
async def download_report(client_id: str):
    """Generate and download an Excel dispute schedule report."""
    client = get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    excel_path = _generate_excel_report(client_id)
    if not excel_path:
        raise HTTPException(
            status_code=404,
            detail="Could not generate report. Ensure an audit has been run first.",
        )

    filename = Path(excel_path).name
    return FileResponse(
        path=excel_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ══════════════════════════════════════════════════════════════════
# Health Check
# ══════════════════════════════════════════════════════════════════


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "1st 4 Mobile Backend",
        "version": "1.0.0",
    }


# ══════════════════════════════════════════════════════════════════
# Startup Event
# ══════════════════════════════════════════════════════════════════


@app.on_event("startup")
async def startup():
    logger.info("=" * 60)
    logger.info("1st 4 Mobile Backend Server starting")
    logger.info(f"  WWW dir:     {WWW_DIR}")
    logger.info(f"  Uploads dir: {UPLOADS_DIR}")
    logger.info(f"  Contracts:   {CONTRACTS_DIR}")
    logger.info(f"  Output dir:  {OUTPUT_DIR}")
    logger.info(f"  Data dir:    {DATA_DIR}")
    logger.info("=" * 60)
