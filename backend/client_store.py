"""Simple file-based client data store.

Each client is stored as a JSON file in the data/ directory.
The store is synchronised (blocking I/O) — suitable for a single
process FastAPI server with moderate throughput.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger("1st4backend.client_store")

# ── Data directory ────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent / "data"
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
CONTRACTS_DIR = Path(__file__).resolve().parent.parent / "contracts"


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)


def _client_path(client_id: str) -> Path:
    return DATA_DIR / f"{client_id}.json"


def create_client(data: dict) -> str:
    """Create a new client record and return its UUID."""
    _ensure_dirs()
    client_id = str(uuid.uuid4())

    record = {
        "client_id": client_id,
        "company_name": data.get("company_name", ""),
        "abn": data.get("abn", ""),
        "industry": data.get("industry", ""),
        "fleet_size": data.get("fleet_size", 0),
        "primary_carrier": data.get("primary_carrier", "Telstra"),
        "email": data.get("email", ""),
        "authorized": False,
        "signed_by": None,
        "has_results": False,
        "created_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }

    path = _client_path(client_id)
    with open(path, "w") as f:
        json.dump(record, f, indent=2)
    logger.info(f"Created client {client_id} ({data.get('company_name', 'N/A')})")
    return client_id


def get_client(client_id: str) -> Optional[dict]:
    """Retrieve a client record by ID. Returns None if not found."""
    path = _client_path(client_id)
    if not path.exists():
        logger.warning(f"Client {client_id} not found")
        return None
    with open(path, "r") as f:
        return json.load(f)


def update_client(client_id: str, updates: dict) -> Optional[dict]:
    """Update fields on an existing client record."""
    record = get_client(client_id)
    if record is None:
        return None
    record.update(updates)
    path = _client_path(client_id)
    with open(path, "w") as f:
        json.dump(record, f, indent=2)
    logger.info(f"Updated client {client_id}")
    return record


def save_authorization(client_id: str, signature_data: str, signed_by: str) -> bool:
    """Save a client's authorisation (signature)."""
    client = get_client(client_id)
    if client is None:
        return False

    # Save signature PNG
    import base64
    import re

    # Strip data URI prefix if present
    if signature_data.startswith("data:image/png;base64,"):
        signature_data = signature_data.replace("data:image/png;base64,", "")
    elif signature_data.startswith("data:"):
        # Handle other MIME types
        signature_data = re.sub(r"^data:[^;]+;base64,", "", signature_data)

    client_upload_dir = UPLOADS_DIR / client_id
    client_upload_dir.mkdir(parents=True, exist_ok=True)

    sig_path = client_upload_dir / "signature.png"
    try:
        # Fix base64 padding
        padding = 4 - len(signature_data) % 4
        if padding != 4:
            signature_data += "=" * padding
        sig_bytes = base64.b64decode(signature_data)
        with open(sig_path, "wb") as f:
            f.write(sig_bytes)
        logger.info(f"Saved signature for client {client_id} to {sig_path}")
    except Exception as exc:
        logger.error(f"Failed to decode/save signature for {client_id}: {exc}")
        return False

    return update_client(client_id, {
        "authorized": True,
        "signed_by": signed_by,
        "authorized_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }) is not None


def get_results(client_id: str) -> Optional[dict]:
    """Return cached audit results for a client, or None."""
    path = DATA_DIR / f"{client_id}_results.json"
    if not path.exists():
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error(f"Failed to read results for {client_id}: {exc}")
        return None


def save_results(client_id: str, results: dict) -> None:
    """Persist audit results to the data store."""
    _ensure_dirs()
    path = DATA_DIR / f"{client_id}_results.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    update_client(client_id, {"has_results": True})
    logger.info(f"Saved results for client {client_id}")


def list_uploads(client_id: str) -> list[str]:
    """Return list of absolute file paths for a client's uploads."""
    client_dir = UPLOADS_DIR / client_id
    if not client_dir.exists():
        return []
    return [str(p) for p in sorted(client_dir.iterdir()) if p.is_file() and p.name != "signature.png"]


def delete_client(client_id: str) -> bool:
    """Remove a client record. Returns True if deleted, False if not found."""
    path = _client_path(client_id)
    if not path.exists():
        return False
    path.unlink()
    logger.info(f"Deleted client {client_id}")
    return True
