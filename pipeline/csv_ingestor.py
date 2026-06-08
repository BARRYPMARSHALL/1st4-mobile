"""
1st 4 Mobile — CSV Ingestor
Auto-detecting CSV parser with support for multi-header rows,
encoding detection, provider fingerprinting, and streaming reads.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from pipeline.config import (
    CSV_CHUNK_SIZE,
    CSV_MAX_FILE_SIZE_MB,
    TELSTRA_FINGERPRINTS,
    OPTUS_FINGERPRINTS,
)

logger = logging.getLogger("1st4pipeline.csv_ingestor")

# Delimiters to try, in priority order
CANDIDATE_DELIMITERS = [",", "\t", "|", ";"]

# Encodings to try, in priority order
CANDIDATE_ENCODINGS = ["utf-8", "latin-1", "cp1252"]


def _detect_delimiter(file_path: str | Path, n_lines: int = 5) -> str:
    """Auto-detect CSV delimiter by counting occurrences in first N lines.

    The delimiter with the most consistent count across lines wins.
    Falls back to comma.
    """
    file_path = Path(file_path)
    lines = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            for _ in range(n_lines):
                line = fh.readline()
                if not line:
                    break
                lines.append(line.rstrip("\n").rstrip("\r"))
    except Exception:
        pass

    if not lines:
        return ","

    best_delim = ","
    best_score = -1

    for delim in CANDIDATE_DELIMITERS:
        counts = [line.count(delim) for line in lines if line.strip()]
        if not counts:
            continue
        # Consistency: low stddev * high mean = good candidate
        n = len(counts)
        if n == 0:
            continue
        mean = sum(counts) / n
        if mean == 0:
            continue
        variance = sum((c - mean) ** 2 for c in counts) / n
        stddev = variance ** 0.5
        # Score: prefer higher mean, penalise variance
        score = mean / (stddev + 1)
        if score > best_score:
            best_score = score
            best_delim = delim

    # Sanity: if best delimiter appears 0 times, default to comma
    if all(line.count(best_delim) == 0 for line in lines if line.strip()):
        return ","

    return best_delim


def _detect_encoding(file_path: str | Path) -> str:
    """Auto-detect file encoding via trial reads.

    Tries UTF-8 → latin-1 → cp1252, returns first that decodes
    the first 8 KB without error.
    """
    file_path = Path(file_path)
    raw = file_path.read_bytes()[:8192]

    for enc in CANDIDATE_ENCODINGS:
        try:
            raw.decode(enc)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue

    return "utf-8"  # safest fallback — pd.read_csv handles errors


def _fingerprint_provider(headers: list[str]) -> str:
    """Detect telecom provider from column header text.

    Returns 'telstra', 'optus', or 'unknown'.
    """
    header_text = " ".join(h.lower() for h in headers if h)

    telstra_hits = sum(
        1 for f in TELSTRA_FINGERPRINTS if f.lower() in header_text
    )
    optus_hits = sum(
        1 for f in OPTUS_FINGERPRINTS if f.lower() in header_text
    )

    if telstra_hits > optus_hits:
        return "telstra"
    elif optus_hits > telstra_hits:
        return "optus"

    # Fall back to per-column substring matching
    for h in headers:
        hl = h.lower().strip()
        for f in TELSTRA_FINGERPRINTS:
            if f.lower() in hl:
                return "telstra"
        for f in OPTUS_FINGERPRINTS:
            if f.lower() in hl:
                return "optus"

    return "unknown"


def _count_header_rows(file_path: str | Path, delimiter: str,
                       encoding: str) -> int:
    """Detect whether CSV has 1 or 2 header rows.

    Heuristic: peek at first 10 lines. If line 2 (0-indexed) contains
    mostly numeric column-like values or matches known header keywords,
    assume single header row. Otherwise check if line 2 looks like
    a sub-header (e.g. units row).
    """
    file_path = Path(file_path)
    lines = []
    try:
        with open(file_path, "r", encoding=encoding, errors="replace") as fh:
            for _ in range(10):
                line = fh.readline()
                if not line:
                    break
                lines.append(line.rstrip("\n").rstrip("\r"))
    except Exception:
        return 1

    if len(lines) < 2:
        return 1

    cols_line1 = [c.strip() for c in lines[0].split(delimiter)]
    cols_line2 = [c.strip() for c in lines[1].split(delimiter)]

    # If line 1 has very few columns, likely metadata, not header
    if len(cols_line1) < 3:
        return 2 if len(cols_line1) > 0 and len(lines) > 1 else 1

    # If line 2 contains mostly empty cells or unit-like text (MB, GB, $)
    unit_keywords = {"mb", "gb", "$", "inc", "gst", "excl", "units",
                     "minutes", "sms", "count", "qty"}
    line2_words = set(
        w for cell in cols_line2
        for w in cell.lower().replace("/", " ").split()
    )
    unit_ratio = len(line2_words & unit_keywords) / max(len(line2_words), 1)

    # If line 1 has typical header keywords and line 2 looks like units/metadata
    header_keywords = {"account", "service", "charge", "plan", "invoice",
                       "description", "amount", "usage", "rate", "date",
                       "period", "number", "name", "code"}
    line1_words = set(
        w for cell in cols_line1
        for w in cell.lower().replace("/", " ").split()
    )
    header_ratio = len(line1_words & header_keywords) / max(len(line1_words), 1)

    if header_ratio > 0.3 and unit_ratio > 0.3:
        return 2

    return 1


def ingest_csv(file_path: str | Path,
               chunk_size: Optional[int] = None) -> tuple:
    """Ingest a CSV file with full auto-detection pipeline.

    Args:
        file_path: Path to the CSV file.
        chunk_size: Override CSV_CHUNK_SIZE from config (None = use default).

    Returns:
        Tuple of (DataFrame, audit_info_dict). The DataFrame contains all
        rows from the file. audit_info has: source_file, rows, columns,
        provider, n_header_rows, delimiter, encoding.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is too large or empty.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    # File size check
    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > CSV_MAX_FILE_SIZE_MB:
        raise ValueError(
            f"CSV file {file_path.name} is {size_mb:.1f} MB, "
            f"exceeds limit of {CSV_MAX_FILE_SIZE_MB} MB"
        )

    # Step 1: detect encoding
    encoding = _detect_encoding(file_path)
    logger.debug(f"Detected encoding: {encoding} for {file_path.name}")

    # Step 2: detect delimiter
    delimiter = _detect_delimiter(file_path)
    logger.debug(f"Detected delimiter: {repr(delimiter)} for {file_path.name}")

    # Step 3: detect header row count
    n_header_rows = _count_header_rows(file_path, delimiter, encoding)
    logger.debug(f"Detected header rows: {n_header_rows} for {file_path.name}")

    header_row = n_header_rows - 1  # pandas is 0-indexed

    # Step 4: read the file (streaming via chunks if large, then concat)
    actual_chunk_size = chunk_size or CSV_CHUNK_SIZE

    # Read header separately so we can fingerprint
    header_df = pd.read_csv(
        file_path,
        delimiter=delimiter,
        encoding=encoding,
        nrows=0,  # only read header
        header=header_row,
        on_bad_lines="warn",
        engine="python",
    )
    raw_headers = list(header_df.columns)
    provider = _fingerprint_provider(raw_headers)
    logger.info(
        f"Provider fingerprint: {provider} for {file_path.name}"
    )

    # Check if file is empty (no data rows after header)
    total_rows_estimate = max(0, sum(1 for _ in open(file_path, "rb")) - n_header_rows - 1)
    if total_rows_estimate == 0:
        raise ValueError(f"CSV file {file_path.name} has no data rows")

    # Step 5: streaming read
    chunks = []
    try:
        for chunk in pd.read_csv(
            file_path,
            delimiter=delimiter,
            encoding=encoding,
            chunksize=actual_chunk_size,
            header=header_row,
            on_bad_lines="warn",
            engine="python",
            dtype=str,  # read all as strings to preserve precision
            keep_default_na=False,
        ):
            chunks.append(chunk)
    except Exception as exc:
        logger.error(f"Error reading CSV {file_path.name}: {exc}")
        raise

    if not chunks:
        raise ValueError(f"No data could be read from {file_path.name}")

    df = pd.concat(chunks, ignore_index=True)

    # Clean up column names
    df.columns = [str(c).strip() for c in df.columns]
    # Remove entirely empty columns
    df = df.dropna(axis=1, how="all")

    # Strip whitespace from all string cells
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    rows, cols = df.shape

    audit_info = {
        "source_file": str(file_path.resolve()),
        "rows": rows,
        "columns": cols,
        "provider": provider,
        "n_header_rows": n_header_rows,
        "delimiter": delimiter,
        "encoding": encoding,
        "column_names": list(df.columns),
    }

    logger.info(
        f"Ingested {file_path.name}: {rows} rows × {cols} cols, "
        f"provider={provider}, delimiter={repr(delimiter)}"
    )

    return df, audit_info
