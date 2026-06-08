"""
1st 4 Mobile — Ghost Line Detector

Identifies ghost lines — services that are being billed but not delivering
value. Three detection signals:
  1. Zero usage for N+ consecutive months
  2. Disconnect/cancellation fee charged but billing continues
  3. Never used (bill-only activation with zero usage history)
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np

import pipeline.config as config
from pipeline.contract_matrix import ContractMatrix
from pipeline.utils.logging_utils import AuditLogger

logger = logging.getLogger("1st4pipeline.detect_ghost")

# Minimum months of history to consider "never used"
NEVER_USED_MIN_MONTHS = 3


def _exclude_row(cat: str, stype: str) -> bool:
    """Return True if a row should be excluded from ghost analysis."""
    # Exclude fixed line services
    if stype and stype.lower() in ("fixed_line", "fixed"):
        return True
    # Exclude equipment charges
    if cat and cat.lower() == "equipment":
        return True
    return False


def _detect_zero_usage(
    df: pd.DataFrame,
    months_required: int,
    audit: Optional[AuditLogger],
) -> pd.DataFrame:
    """Signal 1: service_id with usage_units == 0 for consecutive months."""
    rows: list[dict] = []

    # Filter to rows that have usage data and are not excluded
    usage_df = df[df["charge_category"].isin(("usage", "roaming", "overage"))].copy()
    if usage_df.empty:
        logger.debug("Zero-usage check: no usage rows found")
        return pd.DataFrame(rows)

    # Ensure charge_period_start is date
    usage_df["_period"] = pd.to_datetime(usage_df["charge_period_start"], errors="coerce")
    usage_df = usage_df.dropna(subset=["_period"])
    usage_df = usage_df.sort_values(["service_id", "_period"])

    for service_id, grp in usage_df.groupby("service_id"):
        grp = grp.sort_values("_period")
        # Mark rows with zero usage
        has_usage = grp["usage_units"].apply(
            lambda x: pd.notna(x) and float(x) > 0
        )
        zero_streak = 0
        for idx in range(len(grp)):
            if not has_usage.iloc[idx]:
                zero_streak += 1
            else:
                zero_streak = 0
            if zero_streak >= months_required:
                # This service qualifies: find latest monthly_access fee
                service_rows = df[df["service_id"] == service_id]
                access_rows = service_rows[
                    service_rows["charge_category"] == "monthly_access"
                ]
                total_access = float(access_rows["charge_amount"].sum() or 0)
                # Estimate monthly overcharge: latest monthly_access, or avg
                monthly = 0.0
                if not access_rows.empty:
                    valid_amts = access_rows["charge_amount"].dropna()
                    if not valid_amts.empty:
                        monthly = float(valid_amts.iloc[-1]) if len(valid_amts) > 0 else 0.0
                rows.append({
                    "service_id": service_id,
                    "detection_method": "zero_usage",
                    "confidence": 0.85,
                    "total_access_fees_billed": round(total_access, 2),
                    "estimated_monthly_overcharge": round(monthly, 2),
                    "detail": (
                        f"Zero usage for {zero_streak} consecutive months "
                        f"(threshold: {months_required})"
                    ),
                })
                # Only flag once per service
                break

    if audit:
        audit.log(
            "ghost_detect", "zero_usage",
            f"Found {len(rows)} services with zero usage",
            count=len(rows),
        )
    logger.info(f"Zero-usage ghost lines detected: {len(rows)}")
    return pd.DataFrame(rows)


def _detect_disconnect_continued_billing(
    df: pd.DataFrame,
    audit: Optional[AuditLogger],
) -> pd.DataFrame:
    """Signal 2: disconnect fee charged but monthly_access continues."""
    rows: list[dict] = []

    # Find services with disconnect charges
    disconnect_df = df[df["charge_category"] == "disconnect"].copy()
    if disconnect_df.empty:
        logger.debug("Disconnect check: no disconnect rows found")
        return pd.DataFrame(rows)

    grouped = disconnect_df.groupby("service_id")
    for service_id, disconn_grp in grouped:
        service_rows = df[df["service_id"] == service_id].copy()
        service_rows["_period"] = pd.to_datetime(
            service_rows["charge_period_start"], errors="coerce"
        )
        service_rows = service_rows.dropna(subset=["_period"])

        # Get the latest disconnect date
        disconn_grp["_period"] = pd.to_datetime(
            disconn_grp["charge_period_start"], errors="coerce"
        )
        disconn_grp = disconn_grp.dropna(subset=["_period"])
        max_disconnect_date = disconn_grp["_period"].max()

        # Find monthly_access charges after the disconnect date
        post_disconnect = service_rows[
            (service_rows["charge_category"] == "monthly_access")
            & (service_rows["_period"] >= max_disconnect_date)
        ]
        if not post_disconnect.empty:
            total_access = float(post_disconnect["charge_amount"].sum() or 0)
            monthly = float(
                post_disconnect["charge_amount"].dropna().iloc[-1]
                if not post_disconnect["charge_amount"].dropna().empty
                else 0.0
            )
            rows.append({
                "service_id": service_id,
                "detection_method": "disconnect_but_billing",
                "confidence": 0.95,
                "total_access_fees_billed": round(total_access, 2),
                "estimated_monthly_overcharge": round(monthly, 2),
                "detail": (
                    f"Disconnect/cancellation fee charged on "
                    f"{max_disconnect_date.date()} but monthly access "
                    f"billing continues ({len(post_disconnect)} period(s))"
                ),
            })

    if audit:
        audit.log(
            "ghost_detect", "disconnect_billing",
            f"Found {len(rows)} services with disconnect but continued billing",
            count=len(rows),
        )
    logger.info(f"Disconnect-but-billing ghost lines detected: {len(rows)}")
    return pd.DataFrame(rows)


def _detect_never_used(
    df: pd.DataFrame,
    audit: Optional[AuditLogger],
) -> pd.DataFrame:
    """Signal 3: billing for 3+ months with zero usage ever (bill-only)."""
    rows: list[dict] = []

    # Identify services with monthly_access charges
    access_df = df[df["charge_category"] == "monthly_access"].copy()
    if access_df.empty:
        logger.debug("Never-used check: no monthly_access rows found")
        return pd.DataFrame(rows)

    # Count distinct billing periods per service
    access_df["_period"] = pd.to_datetime(
        access_df["charge_period_start"], errors="coerce"
    )
    access_df = access_df.dropna(subset=["_period"])

    billing_months = (
        access_df.groupby("service_id")["_period"]
        .nunique()
        .reset_index()
        .rename(columns={"_period": "billing_months"})
    )
    qualified = billing_months[billing_months["billing_months"] >= NEVER_USED_MIN_MONTHS]

    for _, row in qualified.iterrows():
        sid = row["service_id"]

        # Check if this service has ever had any usage
        usage_rows = df[
            (df["service_id"] == sid)
            & (df["charge_category"].isin(("usage", "roaming", "overage")))
        ]
        total_usage = usage_rows["usage_units"].apply(
            lambda x: float(x) if pd.notna(x) else 0.0
        ).sum()

        if total_usage <= 0:
            service_rows = df[df["service_id"] == sid]
            access = service_rows[
                service_rows["charge_category"] == "monthly_access"
            ]
            total_access = float(access["charge_amount"].sum() or 0)
            monthly = float(
                access["charge_amount"].dropna().iloc[-1]
                if not access["charge_amount"].dropna().empty
                else 0.0
            )
            rows.append({
                "service_id": sid,
                "detection_method": "never_used",
                "confidence": 0.80,
                "total_access_fees_billed": round(total_access, 2),
                "estimated_monthly_overcharge": round(monthly, 2),
                "detail": (
                    f"Billing for {int(row['billing_months'])} months "
                    f"with zero usage ever (bill-only activation)"
                ),
            })

    if audit:
        audit.log(
            "ghost_detect", "never_used",
            f"Found {len(rows)} services with zero usage ever",
            count=len(rows),
        )
    logger.info(f"Never-used ghost lines detected: {len(rows)}")
    return pd.DataFrame(rows)


def detect_ghost_lines(
    df: pd.DataFrame,
    contract: ContractMatrix,
    months_required: Optional[int] = None,
    audit: Optional[AuditLogger] = None,
) -> pd.DataFrame:
    """Run all ghost line detection signals and return combined results.

    Args:
        df: Normalised invoice DataFrame (canonical schema).
        contract: ContractMatrix instance for plan lookups.
        months_required: Override for GHOST_ZERO_USAGE_MONTHS threshold.
        audit: Optional AuditLogger for audit trail.

    Returns:
        DataFrame with columns:
            service_id, detection_method, confidence,
            total_access_fees_billed, estimated_monthly_overcharge, detail
    """
    if df.empty:
        logger.warning("detect_ghost_lines called with empty DataFrame")
        return pd.DataFrame(columns=[
            "service_id", "detection_method", "confidence",
            "total_access_fees_billed", "estimated_monthly_overcharge", "detail",
        ])

    zero_months = months_required if months_required is not None else config.GHOST_ZERO_USAGE_MONTHS

    logger.info(
        f"Running ghost line detection on {len(df)} rows "
        f"(zero-usage threshold={zero_months} months)"
    )

    # Exclude fixed lines and equipment from all signals
    df_filtered = df[
        ~df.apply(
            lambda r: _exclude_row(
                str(r.get("charge_category", "") or ""),
                str(r.get("service_type", "") or ""),
            ),
            axis=1,
        )
    ].copy()

    results: list[pd.DataFrame] = []

    # Signal 1: Zero usage
    zero_df = _detect_zero_usage(df_filtered, zero_months, audit)
    if not zero_df.empty:
        results.append(zero_df)

    # Signal 2: Disconnect + continued billing
    disconnect_df = _detect_disconnect_continued_billing(df_filtered, audit)
    if not disconnect_df.empty:
        results.append(disconnect_df)

    # Signal 3: Never used
    never_df = _detect_never_used(df_filtered, audit)
    if not never_df.empty:
        results.append(never_df)

    if not results:
        logger.info("No ghost lines detected")
        return pd.DataFrame(columns=[
            "service_id", "detection_method", "confidence",
            "total_access_fees_billed", "estimated_monthly_overcharge", "detail",
        ])

    combined = pd.concat(results, ignore_index=True)

    # Drop duplicate service_id entries (keep highest confidence)
    combined = combined.sort_values("confidence", ascending=False)
    combined = combined.drop_duplicates(subset=["service_id"], keep="first")
    combined = combined.reset_index(drop=True)

    total_monthly = combined["estimated_monthly_overcharge"].sum()
    logger.info(
        f"Ghost detection complete: {len(combined)} lines flagged, "
        f"estimated monthly overcharge=${total_monthly:.2f}"
    )

    if audit:
        audit.log(
            "ghost_detect", "total",
            f"Total ghost lines: {len(combined)}",
            count=len(combined),
            amount=round(total_monthly, 2),
        )

    return combined
