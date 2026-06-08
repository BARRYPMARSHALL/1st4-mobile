"""
1st 4 Mobile — Schema Normalisation Engine

Maps raw ingestion DataFrames to the 18-field canonical schema.
Uses column_mappings.yaml for direct matches and fuzzy_column_match()
as fallback for unmapped columns. Classifies service_type and
charge_category using text_utils functions, parses dates and amounts,
and handles GST detection/stripping.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from pipeline.config import COLUMN_MAPPINGS_PATH
from pipeline.utils.date_utils import parse_date
from pipeline.utils.money_utils import parse_amount, is_gst_inclusive, strip_gst
from pipeline.utils.text_utils import (
    fuzzy_column_match,
    classify_service_type,
    classify_charge_category,
    clean_string,
)

logger = logging.getLogger("1st4pipeline.normaliser")

# The 18-field canonical schema
CANONICAL_SCHEMA = [
    "account_number",
    "service_id",
    "service_type",
    "charge_description",
    "charge_category",
    "charge_amount",
    "usage_units",
    "rate_per_unit",
    "plan_code",
    "plan_name",
    "charge_period_start",
    "charge_period_end",
    "invoice_number",
    "billed_quantity",
    "billed_rate",
    "source_file",
    "source_row",
]

# Amount fields that may need GST stripping
GST_SENSITIVE_FIELDS = {"charge_amount", "billed_rate", "rate_per_unit"}


def _load_column_mappings() -> dict:
    """Load the column mapping YAML file.

    Returns:
        Dict with two top-level keys: 'telstra_patterns' and 'optus_patterns'.
        Each is a list with one dict containing 'provider' and 'patterns'.

    Raises:
        FileNotFoundError: If the mapping file doesn't exist.
        ValueError: If the YAML is malformed.
    """
    path = Path(COLUMN_MAPPINGS_PATH)
    if not path.exists():
        raise FileNotFoundError(
            f"Column mappings file not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as fh:
        mappings = yaml.safe_load(fh)

    if not mappings:
        raise ValueError(f"Empty or invalid column mappings YAML at {path}")

    return mappings


def _build_pattern_lookup(mappings: dict,
                          provider: str) -> dict[str, list[str]]:
    """Build a {canonical_field: [known_column_names]} lookup dict.

    Args:
        mappings: Raw loaded mappings dict.
        provider: 'telstra' or 'optus' or 'unknown'.

    Returns:
        Dict mapping each canonical field to a list of known column name
        patterns. Falls back to Telstra patterns for unknown providers.
    """
    patterns: dict[str, list[str]] = {}

    # Prefer provider-specific patterns
    for provider_key in [f"{provider}_patterns", "telstra_patterns"]:
        provider_data = mappings.get(provider_key, [])
        if isinstance(provider_data, list) and provider_data:
            patterns_dict = provider_data[0].get("patterns", {})
            if isinstance(patterns_dict, dict):
                for field, aliases in patterns_dict.items():
                    if field in CANONICAL_SCHEMA:
                        if field not in patterns:
                            patterns[field] = []
                        patterns[field].extend(aliases)
                # If we loaded something, move on
                break

    return patterns


def _map_columns(raw_columns: list[str],
                 pattern_lookup: dict[str, list[str]],
                 provider: str) -> dict[str, str]:
    """Map raw column names to canonical field names.

    For each canonical field, checks:
    1. Exact match in known patterns
    2. Case-insensitive match
    3. Substring match
    4. fuzzy_column_match() fallback

    Returns:
        Dict of {raw_column: canonical_field} for matched columns.
    """
    mapping: dict[str, str] = {}
    matched_raw: set[str] = set()

    for raw_col in raw_columns:
        if not raw_col or raw_col.strip() == "":
            continue
        raw_clean = clean_string(raw_col)

        # Check each canonical field's patterns
        best_match = None
        best_field = None

        for field, aliases in pattern_lookup.items():
            if not aliases:
                continue

            # Exact match (case-insensitive)
            for alias in aliases:
                if raw_clean.lower() == alias.lower().strip():
                    best_match = raw_col
                    best_field = field
                    break

            if best_match:
                break

            # Substring match
            for alias in aliases:
                alias_lower = alias.lower().strip()
                raw_lower = raw_clean.lower()
                if alias_lower in raw_lower or raw_lower in alias_lower:
                    best_match = raw_col
                    best_field = field
                    break

            if best_match:
                break

        if best_match:
            mapping[best_match] = best_field
            matched_raw.add(best_match)
        else:
            # Fuzzy fallback
            for field, aliases in pattern_lookup.items():
                if not aliases:
                    continue
                matched = fuzzy_column_match(raw_clean, aliases)
                if matched:
                    mapping[raw_col] = field
                    matched_raw.add(raw_col)
                    break

    return mapping


def _classify_columns(raw_columns: list[str],
                      unmatched: list[str],
                      mapping: dict[str, str],
                      df: pd.DataFrame) -> dict[str, str]:
    """Second pass: classify unmatched columns using heuristics.

    Checks for columns that look like dates, amounts, quantities, etc.
    based on their name and sample values.

    Returns:
        Updated mapping dict.
    """
    remaining = [c for c in unmatched if c not in mapping]

    for col in remaining:
        col_lower = col.lower().strip()

        # Date-like column names
        if any(w in col_lower for w in ["date", "from", "to", "start",
                                        "end", "period", "month"]):
            # Sample first non-null value
            sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else ""
            parsed = parse_date(str(sample))
            if parsed:
                if any(w in col_lower for w in ["from", "start"]):
                    mapping[col] = "charge_period_start"
                elif any(w in col_lower for w in ["to", "end"]):
                    mapping[col] = "charge_period_end"
                else:
                    # Ambiguous — try to infer from context
                    mapping[col] = "charge_period_start"
                continue

        # Amount-like column names
        if any(w in col_lower for w in ["amount", "charge", "fee",
                                         "total", "cost", "price",
                                         "payment"]):
            sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else ""
            parsed = parse_amount(sample)
            if parsed is not None:
                mapping[col] = "charge_amount"
                continue

        # Quantity-like column names
        if any(w in col_lower for w in ["qty", "quantity", "count",
                                         "units", "usage"]):
            mapping[col] = "billed_quantity"
            continue

        # Description-like column names
        if any(w in col_lower for w in ["desc", "detail", "item",
                                         "service", "product"]):
            mapping[col] = "charge_description"
            continue

        # ID-like (short, numeric/code patterns)
        if any(w in col_lower for w in ["id", "code", "number", "num",
                                         "identifier"]):
            mapping[col] = "service_id"
            continue

    return mapping


def normalise(df_raw: pd.DataFrame,
              source_file: str = "",
              provider: str = "unknown") -> tuple:
    """Normalise a raw ingestion DataFrame to the 18-field canonical schema.

    Args:
        df_raw: Raw DataFrame from an ingestor.
        source_file: Original file path (for audit trail).
        provider: 'telstra', 'optus', or 'unknown'.

    Returns:
        Tuple of (canonical_df, unmapped_columns_list).
        canonical_df has exactly the 18 canonical columns (some may be
        all-NaN if no mapping was found). unmapped_columns_list contains
        the names of raw columns that could not be mapped to any canonical
        field.
    """
    if df_raw.empty:
        logger.warning("normalise() received empty DataFrame")
        empty_df = pd.DataFrame(columns=CANONICAL_SCHEMA)
        return empty_df, []

    raw_columns = list(df_raw.columns)
    logger.info(
        f"Normalising {len(df_raw)} rows × {len(raw_columns)} cols "
        f"from {source_file}"
    )

    # Step 1: Load column mappings
    try:
        mappings = _load_column_mappings()
    except (FileNotFoundError, ValueError) as exc:
        logger.warning(f"Could not load column mappings: {exc}")
        mappings = {}

    # Step 2: Build pattern lookup
    pattern_lookup = _build_pattern_lookup(mappings, provider)
    if not pattern_lookup:
        logger.warning(
            f"No patterns found for provider '{provider}', "
            f"trying Telstra patterns as fallback"
        )
        pattern_lookup = _build_pattern_lookup(mappings, "telstra")

    # Step 3: Map columns
    mapping = _map_columns(raw_columns, pattern_lookup, provider)

    # Step 4: Classify unmatched columns via heuristics
    unmatched = [c for c in raw_columns if c not in mapping]
    if unmatched:
        logger.debug(f"Unmatched columns before heuristic pass: {unmatched}")
        mapping = _classify_columns(raw_columns, unmatched, mapping, df_raw)

    # Step 5: Build unmapped columns list
    unmapped_columns = [c for c in raw_columns if c not in mapping]
    if unmapped_columns:
        logger.info(f"Unmapped columns: {unmapped_columns}")
    else:
        logger.info("All columns mapped successfully")

    logger.info(f"Column mapping ({len(mapping)} matches): {mapping}")

    # Step 6: Build canonical DataFrame
    canonical_data: dict[str, list] = {field: [] for field in CANONICAL_SCHEMA}

    for idx in range(len(df_raw)):
        row = df_raw.iloc[idx]

        # Map raw columns to canonical fields
        row_data: dict[str, Optional[object]] = {
            field: None for field in CANONICAL_SCHEMA
        }

        for raw_col, canonical_field in mapping.items():
            if raw_col in df_raw.columns:
                raw_val = row.get(raw_col, None)
                # Convert to string for processing
                val_str = str(raw_val) if pd.notna(raw_val) else ""
                row_data[canonical_field] = raw_val

        # Step 7: Parse dates
        period_start_raw = row_data.get("charge_period_start")
        if period_start_raw is not None and pd.notna(period_start_raw):
            row_data["charge_period_start"] = parse_date(str(period_start_raw))

        period_end_raw = row_data.get("charge_period_end")
        if period_end_raw is not None and pd.notna(period_end_raw):
            row_data["charge_period_end"] = parse_date(str(period_end_raw))

        # Step 8: Parse amounts
        charge_raw = row_data.get("charge_amount")
        if charge_raw is not None and pd.notna(charge_raw):
            row_data["charge_amount"] = parse_amount(str(charge_raw))
        else:
            row_data["charge_amount"] = None

        rate_raw = row_data.get("rate_per_unit")
        if rate_raw is not None and pd.notna(rate_raw):
            row_data["rate_per_unit"] = parse_amount(str(rate_raw))
        else:
            row_data["rate_per_unit"] = None

        billed_rate_raw = row_data.get("billed_rate")
        if billed_rate_raw is not None and pd.notna(billed_rate_raw):
            row_data["billed_rate"] = parse_amount(str(billed_rate_raw))
        else:
            row_data["billed_rate"] = None

        # Step 9: Parse billed_quantity as float
        qty_raw = row_data.get("billed_quantity")
        if qty_raw is not None and pd.notna(qty_raw):
            try:
                row_data["billed_quantity"] = float(str(qty_raw).replace(",", ""))
            except (ValueError, TypeError):
                row_data["billed_quantity"] = None

        # Step 10: GST detection and stripping
        charge_amt = row_data.get("charge_amount")
        if charge_amt is not None:
            # Check if the column names for amount fields indicate GST-inclusive
            # We check charge_amount column name
            for raw_col, cf in mapping.items():
                if cf == "charge_amount":
                    sample_val = str(charge_amt)
                    if is_gst_inclusive(raw_col, sample_val):
                        row_data["charge_amount"] = strip_gst(charge_amt)
                        logger.debug(f"Stripped GST from charge_amount: "
                                     f"{charge_amt} → {row_data['charge_amount']}")
                    break

        # Step 11: Classify service_type if not directly mapped
        st = row_data.get("service_type")
        if st is None or (isinstance(st, str) and not st.strip()):
            desc = str(row_data.get("charge_description") or "")
            plan_code = str(row_data.get("plan_code") or "")
            row_data["service_type"] = classify_service_type(desc, plan_code)

        # Step 12: Classify charge_category if not directly mapped
        cc = row_data.get("charge_category")
        if cc is None or (isinstance(cc, str) and not cc.strip()):
            desc = str(row_data.get("charge_description") or "")
            amt = row_data.get("charge_amount") or 0.0
            row_data["charge_category"] = classify_charge_category(desc, amt)

        # Step 13: Set source metadata
        row_data["source_file"] = source_file
        row_data["source_row"] = idx + 1  # 1-indexed row

        # Append
        for field in CANONICAL_SCHEMA:
            canonical_data[field].append(row_data.get(field))

    # Build DataFrame
    canonical_df = pd.DataFrame(canonical_data)

    # Clean service descriptions
    if "charge_description" in canonical_df.columns:
        canonical_df["charge_description"] = (
            canonical_df["charge_description"]
            .apply(lambda x: clean_string(str(x)) if pd.notna(x) else None)
        )

    logger.info(
        f"Normalised to {len(canonical_df)} rows × {len(CANONICAL_SCHEMA)} cols "
        f"({len(unmapped_columns)} unmapped columns)"
    )

    return canonical_df, unmapped_columns
