"""
1st 4 Mobile — Pipeline Configuration
All tunable thresholds and paths in one place.
"""

from pathlib import Path

# ── Project Paths ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
OUTPUT_DIR = PROJECT_ROOT / "output"
RACK_RATES_PATH = PROJECT_ROOT / "rack_rates.yaml"
COLUMN_MAPPINGS_PATH = PROJECT_ROOT / "column_mappings.yaml"

# ── Ingestion ─────────────────────────────────────────────────
CSV_CHUNK_SIZE = 50_000  # rows per chunk for streaming
CSV_MAX_FILE_SIZE_MB = 500  # reject CSVs larger than this
PDF_MAX_PAGES = 500  # reject PDFs with more pages
OCR_DPI = 300  # DPI for OCR pre-processing

# ── Detection Engine Thresholds ────────────────────────────────

# Ghost lines
GHOST_ZERO_USAGE_MONTHS = 2  # consecutive months of zero usage to flag
GHOST_MIN_CONFIDENCE = 0.70  # minimum confidence score for inclusion

# Rate validation
RATE_TOLERANCE_PCT = 0.02  # 2% allowed variance
RATE_TOLERANCE_FIXED = 0.50  # +$0.50 fixed tolerance
OVERAGE_TOLERANCE_PCT = 0.10  # 10% for overage rate comparison

# Roaming
ROAMING_TOLERANCE_PCT = 0.05  # 5% allowed variance on roaming rates

# Legacy rollback
ROLLBACK_MIN_MONTHS = 1  # must have at least 1 month of history
ROLLBACK_PRICE_INCREASE_PCT = 0.10  # 10% price increase to trigger

# Duplicates
DUPE_AMOUNT_TOLERANCE_PCT = 0.10  # 10% amount variance for cross-account dupes

# ── Output ─────────────────────────────────────────────────────
DEFAULT_HISTORICAL_MONTHS = 12  # how far back to estimate recovery
OUTPUT_DATE_FORMAT = "%Y-%m-%d"

# ── Provider Fingerprints ──────────────────────────────────────
TELSTRA_FINGERPRINTS = [
    "service id", "account number", "plan name",
    "t-analyst", "telstra connect",
]

OPTUS_FINGERPRINTS = [
    "mobile number", "billing account", "rate plan",
    "my business", "optus insight",
]
