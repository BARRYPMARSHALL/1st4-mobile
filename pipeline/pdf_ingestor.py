"""
1st 4 Mobile — PDF Ingestor
Multi-engine PDF table extraction with fallback chain:
pdfplumber → Camelot → OCR (pytesseract).

Returns (DataFrame, audit_info_dict) with a confidence flag for OCR mode.
"""

import logging
import re
from pathlib import Path
from typing import Optional

import pandas as pd

from pipeline.config import PDF_MAX_PAGES, OCR_DPI

logger = logging.getLogger("1st4pipeline.pdf_ingestor")


def _merge_page_tables(tables: list) -> list:
    """Merge tables that clearly span a page break.

    Heuristic: if the first row of the next table looks like a continuation
    of the last row of the previous table (same number of columns, and
    the first column of the next table doesn't look like a header), merge
    them.
    """
    if len(tables) < 2:
        return tables

    merged = [tables[0]]
    header_keywords = {
        "account", "service", "charge", "plan", "invoice",
        "description", "amount", "usage", "rate", "date",
        "period", "number", "name", "code", "total",
    }

    for table in tables[1:]:
        prev = merged[-1]
        if not table or not prev:
            merged.append(table)
            continue

        first_row = table[0] if table else []
        last_row = prev[-1] if prev else []

        # Need comparable columns
        if len(first_row) != len(last_row):
            merged.append(table)
            continue

        # Check if first row of new table looks like a header
        first_row_text = " ".join(str(c).lower() for c in first_row if c)
        header_words = set(first_row_text.split())
        match_ratio = len(header_words & header_keywords) / max(len(header_words), 1)

        if match_ratio > 0.4:
            # Looks like a header row — don't merge, but drop it if it's
            # identical to the known header pattern (duplicate header)
            prev_first = prev[0] if prev else []
            if first_row == prev_first:
                # Duplicate header on new page — skip it
                continue
            merged.append(table)
            continue

        # Looks like a continuation — merge
        prev.extend(table)
        merged[-1] = prev

    return merged


def _table_to_dataframe(table_data: list, page_label: str = "") -> pd.DataFrame:
    """Convert a list-of-lists table to a DataFrame.

    First row treated as header, subsequent rows as data.
    Returns empty DataFrame if table has < 2 rows.
    """
    if not table_data or len(table_data) < 2:
        return pd.DataFrame()

    # Try first row as header
    header = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(table_data[0])]
    rows = table_data[1:]

    # Ensure all rows have same column count
    n_cols = len(header)
    normalised = []
    for row in rows:
        if len(row) < n_cols:
            row = list(row) + [""] * (n_cols - len(row))
        elif len(row) > n_cols:
            row = row[:n_cols]
        normalised.append([str(c).strip() for c in row])

    df = pd.DataFrame(normalised, columns=header)

    # Remove rows that are empty or page-footer artifacts
    footer_patterns = [
        r"page\s+\d+", r"^\s*$", r"total\s+$",
        r"continue", r"inclusive of gst",
    ]
    mask = pd.Series([True] * len(df))
    for i, row in df.iterrows():
        row_text = " ".join(str(v).lower() for v in row)
        if any(re.search(p, row_text) for p in footer_patterns):
            mask.at[i] = False

    df = df[mask].reset_index(drop=True)
    return df


# ── PDFPlumber ───────────────────────────────────────────────────


def ingest_pdf_plumber(file_path: str | Path) -> tuple:
    """Extract tables from PDF using pdfplumber.

    Extracts tables from all pages, merges those that span page breaks.

    Returns:
        Tuple of (DataFrame, audit_info). audit_info includes source_file,
        pages_processed, tables_found, and method='pdfplumber'.
        Returns (empty DataFrame, partial audit) on failure.
    """
    file_path = Path(file_path)
    audit = {
        "source_file": str(file_path.resolve()),
        "method": "pdfplumber",
        "pages_processed": 0,
        "tables_found": 0,
        "confidence": "high",
        "error": None,
    }

    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber not installed — skipping")
        audit["error"] = "pdfplumber not installed"
        return pd.DataFrame(), audit

    all_tables_raw = []
    total_pages = 0

    try:
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            if total_pages > PDF_MAX_PAGES:
                logger.warning(
                    f"PDF has {total_pages} pages, exceeds limit of {PDF_MAX_PAGES}"
                )
                audit["error"] = f"too many pages ({total_pages} > {PDF_MAX_PAGES})"
                return pd.DataFrame(), audit

            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 1:
                        all_tables_raw.append(table)
                        audit["tables_found"] += 1
                audit["pages_processed"] += 1
    except Exception as exc:
        logger.warning(f"pdfplumber failed on {file_path.name}: {exc}")
        audit["error"] = str(exc)
        return pd.DataFrame(), audit

    if not all_tables_raw:
        logger.info(f"pdfplumber: no tables found in {file_path.name}")
        return pd.DataFrame(), audit

    # Merge tables that span page breaks
    merged_tables = _merge_page_tables(all_tables_raw)

    # Convert merged tables to DataFrames
    dfs = []
    for i, table in enumerate(merged_tables):
        df_page = _table_to_dataframe(table, page_label=f"table_{i}")
        if not df_page.empty:
            dfs.append(df_page)

    if not dfs:
        return pd.DataFrame(), audit

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.dropna(axis=1, how="all")

    logger.info(
        f"pdfplumber extracted {len(combined)} rows × {len(combined.columns)} cols "
        f"from {file_path.name}"
    )
    return combined, audit


# ── Camelot ──────────────────────────────────────────────────────


def ingest_pdf_camelot(file_path: str | Path) -> tuple:
    """Extract tables from PDF using Camelot.

    Attempts lattice mode first (for bordered tables), then falls back
    to stream mode (for borderless tables).

    Returns:
        Tuple of (DataFrame, audit_info). audit_info includes the method
        used ('camelot_lattice' or 'camelot_stream').
        Returns (empty DataFrame, partial audit) on failure.
    """
    file_path = Path(file_path)
    audit = {
        "source_file": str(file_path.resolve()),
        "method": "camelot",
        "mode": None,
        "tables_found": 0,
        "confidence": "high",
        "error": None,
    }

    try:
        import camelot
    except ImportError:
        logger.warning("camelot-py not installed — skipping")
        audit["error"] = "camelot-py not installed"
        return pd.DataFrame(), audit

    # Try lattice mode first
    for mode in ["lattice", "stream"]:
        try:
            tables = camelot.read_pdf(
                str(file_path),
                pages="all",
                flavor=mode,
                suppress_stdout=True,
            )
            audit["tables_found"] = len(tables)

            if tables and tables.n > 0:
                audit["mode"] = mode
                logger.info(
                    f"Camelot {mode}: found {tables.n} tables in {file_path.name}"
                )

                # Parse tables
                dfs = []
                for table in tables:
                    df = table.df
                    if df.shape[0] >= 2:
                        # First row as header
                        df.columns = [str(c).strip() for c in df.iloc[0]]
                        df = df.iloc[1:].reset_index(drop=True)
                        df = df.dropna(axis=1, how="all")
                        if not df.empty:
                            dfs.append(df)

                if dfs:
                    combined = pd.concat(dfs, ignore_index=True)
                    combined = combined.dropna(axis=1, how="all")
                    logger.info(
                        f"Camelot {mode}: {len(combined)} rows × "
                        f"{len(combined.columns)} cols"
                    )
                    return combined, audit

        except Exception as exc:
            logger.warning(f"Camelot {mode} failed on {file_path.name}: {exc}")
            audit["error"] = str(exc)
            continue

    return pd.DataFrame(), audit


# ── OCR (pytesseract) ────────────────────────────────────────────


def ingest_pdf_ocr(file_path: str | Path) -> tuple:
    """Extract text/table data from PDF using OCR as last resort.

    Converts PDF pages to images (via pdf2image or PyMuPDF), then runs
    pytesseract. Low confidence — use only when pdfplumber and Camelot
    both fail.

    Returns:
        Tuple of (DataFrame, audit_info). audit_info includes
        confidence='low' to flag OCR mode usage.
        Returns (empty DataFrame, partial audit) on failure.
    """
    file_path = Path(file_path)
    audit = {
        "source_file": str(file_path.resolve()),
        "method": "ocr",
        "pages_processed": 0,
        "tables_found": 0,
        "confidence": "low",
        "error": None,
    }

    try:
        import pytesseract
    except ImportError:
        logger.warning("pytesseract not installed — skipping OCR")
        audit["error"] = "pytesseract not installed"
        return pd.DataFrame(), audit

    # Try to import image converter
    pdf_to_images = None
    try:
        from pdf2image import convert_from_path as pdf_to_images
    except ImportError:
        try:
            import fitz  # PyMuPDF

            def pdf_to_images(path, dpi=OCR_DPI):
                doc = fitz.open(str(path))
                images = []
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=dpi)
                    img_data = pix.tobytes("ppm")
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(img_data))
                    images.append(img)
                doc.close()
                return images
        except ImportError:
            logger.warning("Neither pdf2image nor PyMuPDF available — OCR unavailable")
            audit["error"] = "no PDF-to-image library available"
            return pd.DataFrame(), audit

    try:
        images = pdf_to_images(str(file_path), dpi=OCR_DPI)
    except Exception as exc:
        logger.warning(f"PDF-to-image conversion failed: {exc}")
        audit["error"] = str(exc)
        return pd.DataFrame(), audit

    if not images:
        return pd.DataFrame(), audit

    audit["pages_processed"] = len(images)

    all_text = []
    for i, img in enumerate(images):
        try:
            text = pytesseract.image_to_string(
                img,
                config="--psm 6 --oem 3",  # Assume uniform block of text
            )
            if text.strip():
                all_text.append(text.strip())
        except Exception as exc:
            logger.warning(f"OCR failed on page {i + 1}: {exc}")
            continue

    if not all_text:
        return pd.DataFrame(), audit

    full_text = "\n".join(all_text)

    # Try to parse text into a structured table
    # Split into lines, then split by common delimiters
    lines = [line.strip() for line in full_text.split("\n") if line.strip()]

    # Attempt to find tabular data: lines with consistent whitespace gaps
    table_lines = []
    for line in lines:
        # Skip obvious non-table lines
        if re.match(r"^\d+\s*$", line):  # page number
            continue
        if re.search(r"(page|total|invoice|statement)", line, re.IGNORECASE):
            pass  # keep, could be table content
        table_lines.append(line)

    if len(table_lines) < 3:
        return pd.DataFrame(), audit

    # Heuristic: split on 2+ spaces
    parsed_rows = []
    for line in table_lines:
        cells = re.split(r"\s{2,}", line)
        if len(cells) >= 2:
            parsed_rows.append(cells)

    if len(parsed_rows) < 2:
        # Fall back to single-column text dump
        df = pd.DataFrame({"ocr_text": table_lines})
    else:
        # First row as header
        header = parsed_rows[0]
        data = parsed_rows[1:]
        # Normalise column count
        n_cols = len(header)
        normalised = []
        for row in data:
            if len(row) < n_cols:
                row = list(row) + [""] * (n_cols - len(row))
            else:
                row = row[:n_cols]
            normalised.append(row)
        df = pd.DataFrame(normalised, columns=header)

    audit["tables_found"] = len(parsed_rows) if len(parsed_rows) >= 2 else 1

    logger.warning(
        f"OCR extracted {len(df)} rows × {len(df.columns)} cols from "
        f"{file_path.name} — LOW CONFIDENCE"
    )
    return df, audit


# ── Detection Chain ──────────────────────────────────────────────


def detect_and_ingest_pdf(file_path: str | Path) -> tuple:
    """Multi-engine PDF ingestion chain.

    Attempts pdfplumber → Camelot → OCR, returning the first non-empty
    result. This ensures the best available extraction method is used.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Tuple of (DataFrame, audit_info_dict). audit_info includes
        the method used and confidence flag.
        If all methods fail, returns (empty DataFrame, audit_info with error).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    engines = [
        ("pdfplumber", ingest_pdf_plumber),
        ("camelot", ingest_pdf_camelot),
        ("ocr", ingest_pdf_ocr),
    ]

    for engine_name, engine_func in engines:
        logger.info(f"Attempting {engine_name} on {file_path.name}...")
        try:
            df, audit = engine_func(file_path)
            if df is not None and not df.empty:
                audit["engine"] = engine_name
                rows, cols = df.shape
                logger.info(
                    f"{engine_name} succeeded: {rows} rows × {cols} cols"
                )
                return df, audit
        except Exception as exc:
            logger.warning(f"{engine_name} raised exception: {exc}")
            continue

    # All engines failed
    logger.error(f"All PDF engines failed for {file_path.name}")
    return pd.DataFrame(), {
        "source_file": str(file_path.resolve()),
        "engine": "none",
        "error": "all engines failed",
        "rows": 0,
        "columns": 0,
        "confidence": "none",
        "method": "none",
    }
