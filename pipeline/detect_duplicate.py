"""
1st 4 Mobile — Duplicate Service Filter

Detects duplicate service charges on invoices:
  1. Exact duplicates — same service_id + charge_description +
     charge_amount + charge_period_start
  2. Cross-account duplicates — same service_id appearing under
     different account numbers
  3. Near duplicates — same service_id, same charge_category,
     amounts within config.DUPE_AMOUNT_TOLERANCE_PCT
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np

import pipeline.config as config
from pipeline.utils.logging_utils import AuditLogger

logger = logging.getLogger("1st4pipeline.detect_duplicate")


def detect_duplicate_services(
    df: pd.DataFrame,
    audit: Optional[AuditLogger] = None,
) -> pd.DataFrame:
    """Detect duplicate service charges and return flagged rows.

    Three detection methods:
      1. Exact duplicates (exact match on key fields)
      2. Cross-account duplicates (same service_id, different account)
      3. Near duplicates (same service, same category, amounts within %)

    Args:
        df: Normalised invoice DataFrame (canonical schema).
        audit: Optional AuditLogger for audit trail.

    Returns:
        DataFrame with duplicate flags. Each flagged row represents
        a pair of suspected duplicates, with the 'duplicate_of' column
        referencing the original row's service_id.
    """
    rows: list[dict] = []

    if df.empty:
        logger.warning("detect_duplicate_services called with empty DataFrame")
        return _empty_result()

    df = df.reset_index(drop=True)
    logger.info(f"Running duplicate detection on {len(df)} rows")

    # ── Helper: generate a stable row identifier ──────────────────
    df["_idx"] = df.index

    # ── Signal 1: Exact duplicates ────────────────────────────────
    # charge_description is optional; fall back to plan_code + charge_category
    has_desc = "charge_description" in df.columns
    desc_field = "charge_description" if has_desc else "plan_code"
    
    exact_keys = ["service_id", desc_field, "charge_amount",
                  "charge_period_start"]
    exact_df = df[exact_keys + ["_idx"]].copy()

    # Convert charge_period_start to string for hashing
    exact_df["_period_str"] = exact_df["charge_period_start"].apply(
        lambda x: str(x) if pd.notna(x) else ""
    )
    exact_df["_period_str"] = exact_df["_period_str"].fillna("")

    # Create a hashable key
    exact_df["_dup_key"] = (
        exact_df["service_id"].fillna("").astype(str) + "||"
        + exact_df[desc_field].fillna("").astype(str) + "||"
        + exact_df["charge_amount"].fillna(0).astype(str) + "||"
        + exact_df["_period_str"]
    )

    dup_counts = exact_df["_dup_key"].value_counts()
    exact_dup_keys = dup_counts[dup_counts > 1].index

    for dup_key in exact_dup_keys:
        matched_idx = exact_df[exact_df["_dup_key"] == dup_key]["_idx"].tolist()
        original_idx = matched_idx[0]
        for dup_idx in matched_idx[1:]:
            orig_row = df.loc[original_idx]
            dup_row = df.loc[dup_idx]
            rows.append({
                "service_id": dup_row.get("service_id"),
                "account_number": dup_row.get("account_number"),
                "duplicate_of": orig_row.get("service_id"),
                "duplicate_account": orig_row.get("account_number"),
                "detection_method": "exact_duplicate",
                "confidence": 0.98,
                "charge_description": dup_row.get("charge_description"),
                "charge_amount": float(dup_row.get("charge_amount") or 0),
                "charge_category": dup_row.get("charge_category"),
                "detail": (
                    f"Exact duplicate of service '{orig_row.get('service_id')}': "
                    f"same description, amount, and period"
                ),
            })

    if audit:
        audit.log(
            "duplicate_detect", "exact_duplicates",
            f"Found {len([r for r in rows if r['detection_method'] == 'exact_duplicate'])} "
            f"exact duplicates",
            count=len([r for r in rows if r['detection_method'] == 'exact_duplicate']),
        )

    # ── Signal 2: Cross-account duplicates ────────────────────────
    # Same service_id appearing under different account numbers
    if "account_number" in df.columns:
        service_accounts = (
            df.groupby("service_id")["account_number"]
            .apply(lambda x: set(x.dropna().unique()))
        )
        multi_account = service_accounts[service_accounts.apply(len) > 1]
        for sid in multi_account.index:
            sid_rows = df[df["service_id"] == sid]
            accounts = multi_account[sid]
            rows.append({
                "service_id": sid,
                "detection_method": "cross_account_duplicate",
                "confidence": 0.90,
                "charge_amount": float(sid_rows["charge_amount"].iloc[0] or 0),
                "charge_category": sid_rows["charge_category"].iloc[0] if "charge_category" in sid_rows.columns else "",
                "detail": (
                    f"Service '{sid}' appears under {len(accounts)} "
                    f"different account numbers: {', '.join(sorted(accounts))}"
                ),
            })

    # ── Signal 3: Near duplicates ─────────────────────────────────
    # Same service_id, same charge_category, amounts within tolerance
    tolerance_pct = config.DUPE_AMOUNT_TOLERANCE_PCT

    for service_id, grp in df.groupby("service_id"):
        grp = grp.reset_index(drop=True)
        if len(grp) < 2:
            continue

        for category, cat_grp in grp.groupby("charge_category"):
            cat_grp = cat_grp.reset_index(drop=True)
            if len(cat_grp) < 2:
                continue

            amounts = cat_grp["charge_amount"].dropna()
            if len(amounts) < 2:
                continue

            # Compare every pair within the group
            for i in range(len(cat_grp)):
                for j in range(i + 1, len(cat_grp)):
                    row_i = cat_grp.iloc[i]
                    row_j = cat_grp.iloc[j]

                    amt_i = float(row_i.get("charge_amount") or 0)
                    amt_j = float(row_j.get("charge_amount") or 0)

                    if amt_i == 0 and amt_j == 0:
                        continue

                    # Calculate relative difference
                    max_amt = max(abs(amt_i), abs(amt_j))
                    if max_amt == 0:
                        continue
                    diff_pct = abs(amt_i - amt_j) / max_amt * 100.0

                    if diff_pct <= tolerance_pct * 100.0:
                        # Flag the duplicate if not already flagged by exact match
                        rows.append({
                            "service_id": service_id,
                            "account_number": row_j.get("account_number"),
                            "duplicate_of": service_id,
                            "duplicate_account": row_i.get("account_number"),
                            "detection_method": "near_duplicate",
                            "confidence": 0.75,
                            "charge_description": row_j.get("charge_description"),
                            "charge_amount": round(amt_j, 2),
                            "charge_category": category,
                            "detail": (
                                f"Near duplicate in category '{category}': "
                                f"${amt_i:.2f} vs ${amt_j:.2f} "
                                f"({diff_pct:.1f}% difference, "
                                f"tolerance={tolerance_pct*100:.0f}%)"
                            ),
                        })

    if audit:
        audit.log(
            "duplicate_detect", "near_duplicates",
            f"Found {len([r for r in rows if r['detection_method'] == 'near_duplicate'])} "
            f"near duplicates",
            count=len([r for r in rows if r['detection_method'] == 'near_duplicate']),
        )

    # ── Build result DataFrame and deduplicate ────────────────────
    result = pd.DataFrame(rows)
    if not result.empty:
        # Sort by confidence (highest first) and drop duplicate rows
        result = result.sort_values("confidence", ascending=False)
        result = result.drop_duplicates(
            subset=["service_id", "account_number", "charge_description",
                     "charge_amount", "detection_method"],
            keep="first",
        )
        result = result.reset_index(drop=True)

    if audit:
        audit.log(
            "duplicate_detect", "total",
            f"Total duplicate flags: {len(result)}",
            count=len(result),
        )

    logger.info(f"Duplicate detection complete: {len(result)} flags")
    return result


def _empty_result() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "service_id", "account_number", "duplicate_of",
        "duplicate_account", "detection_method", "confidence",
        "charge_description", "charge_amount", "charge_category", "detail",
    ])
