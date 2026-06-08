"""
1st 4 Mobile — FastAPI Backend Server (PostgreSQL edition)

Serves the www/ static frontend and exposes REST APIs for:
  - Client registration and authorisation
  - File upload (CSV, PDF, XLSX)
  - Audit pipeline execution
  - Audit results and dashboard data
  - Excel report download
  - Owner dashboard

Uses async SQLAlchemy + asyncpg for PostgreSQL persistence.
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# ── Project paths ─────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WWW_DIR = PROJECT_ROOT / "www"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
OUTPUT_DIR = PROJECT_ROOT / "output"

# ── Logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
logger = logging.getLogger("1st4backend.server")

# ── Ensure required directories ────────────────────────────────────
for d in [WWW_DIR, UPLOADS_DIR, CONTRACTS_DIR, OUTPUT_DIR]:
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

# ── Register routers ──────────────────────────────────────────────
from backend.owner_routes import router as owner_router
from backend.client_routes import router as client_router

app.include_router(owner_router)
app.include_router(client_router)


# ══════════════════════════════════════════════════════════════════
# Routes — Frontend Pages
# ══════════════════════════════════════════════════════════════════


def _serve_html(filename: str, request: Request) -> HTMLResponse:
    """Serve an HTML file from the www/ directory."""
    path = WWW_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found")
    content = path.read_text(encoding="utf-8")
    return HTMLResponse(content=content)


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
# Health Check
# ══════════════════════════════════════════════════════════════════


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "1st 4 Mobile Backend",
        "version": "1.0.0",
        "database": "postgresql",
    }


# ══════════════════════════════════════════════════════════════════
# Startup Event
# ══════════════════════════════════════════════════════════════════


@app.on_event("startup")
async def startup():
    from backend.database import init_db
    await init_db()
    logger.info("=" * 60)
    logger.info("1st 4 Mobile Backend Server starting (PostgreSQL)")
    logger.info(f"  WWW dir:     {WWW_DIR}")
    logger.info(f"  Uploads dir: {UPLOADS_DIR}")
    logger.info(f"  Contracts:   {CONTRACTS_DIR}")
    logger.info(f"  Output dir:  {OUTPUT_DIR}")
    logger.info("=" * 60)
