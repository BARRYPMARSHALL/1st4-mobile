"""
1st 4 Mobile — Detection Engine Runner

Orchestrates all 5 detection engines and returns a consolidated
result dictionary with a summary of findings.
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np

import pipeline.config as config
from pipeline.contract_matrix import ContractMatrix
from pipeline.utils.logging_utils import AuditLogger

from pipeline.detect_ghost import detect_ghost_lines
from pipeline.detect_rate import (
    detect_rate_mismatches,
    validate_overage_rates,
    validate_discounts,
)
from pipeline.detect_roaming import (
    detect_roaming_anomalies,
    check_roaming_entitlement,
)
from pipeline.detect_legacy import detect_legacy_rollbacks
from pipeline.detect_duplicate import detect_duplicate_services

logger = logging.getLogger("1st4pipeline.detect_runner")


def run_all_detections(
    df: pd.DataFrame,
    contract: ContractMatrix,
    rack_rates: Optional[dict] = None,
    audit: Optional[AuditLogger] = None,
) -> dict:
    """Run all 5 detection engines and consolidate results.

    Args:
        df: Normalised invoice DataFrame (canonical schema).
        contract: ContractMatrix with plan definitions and rates.
        rack_rates: Optional dict of {plan_code: rate} from rack_rates.yaml.
        audit: Optional AuditLogger for audit trail.

    Returns:
        dict with keys:
            ghost_lines       — DataFrame of ghost line flags
            rate_mismatches   — DataFrame of rate mismatch flags
            roaming           — DataFrame of roaming anomaly flags
            legacy_rollbacks  — DataFrame of legacy rollback flags
            duplicates        — DataFrame of duplicate flags
            summary           — dict with:
                total_flags              int
                total_monthly_overcharge float
                total_annualised         float
                breakdown                dict[str, int]  (flags per engine)
                monthly_breakdown        dict[str, float] (per engine)
    """
    if df.empty:
        logger.warning("run_all_detections called with empty DataFrame")
        empty_summary = _build_summary({}, 0.0)
        return {
            "ghost_lines": pd.DataFrame(),
            "rate_mismatches": pd.DataFrame(),
            "roaming": pd.DataFrame(),
            "legacy_rollbacks": pd.DataFrame(),
            "duplicates": pd.DataFrame(),
            "summary": empty_summary,
        }

    logger.info(
        f"Running detection engines on {len(df)} rows, "
        f"contract={contract.client_name}, "
        f"rack_rates={'provided' if rack_rates else 'not provided'}"
    )

    if audit:
        audit.log(
            "detect_runner", "start",
            f"Starting detection engines on {len(df)} rows",
            count=len(df),
        )

    # ── 1. Ghost Lines ────────────────────────────────────────────
    logger.info("─" * 50)
    logger.info("Engine 1/5: Ghost Line Detector")
    try:
        ghost_result = detect_ghost_lines(df, contract, audit=audit)
    except Exception as exc:
        logger.error(f"Ghost line detection failed: {exc}", exc_info=True)
        ghost_result = pd.DataFrame()
    logger.info(f"  → {len(ghost_result)} ghost lines flagged")

    # ── 2. Rate Mismatches ───────────────────────────────────────
    logger.info("Engine 2/5: Rate Plan Validator")
    rate_result = pd.DataFrame()
    overage_result = pd.DataFrame()
    discount_result = pd.DataFrame()
    try:
        rate_result = detect_rate_mismatches(df, contract, audit=audit)
        overage_result = validate_overage_rates(df, contract, audit=audit)
        discount_result = validate_discounts(df, contract, audit=audit)

        # Combine all rate-related flags
        rate_parts = [r for r in [rate_result, overage_result, discount_result]
                      if not r.empty]
        if rate_parts:
            rate_combined = pd.concat(rate_parts, ignore_index=True)
        else:
            rate_combined = pd.DataFrame()
    except Exception as exc:
        logger.error(f"Rate validation failed: {exc}", exc_info=True)
        rate_combined = pd.DataFrame()
    logger.info(f"  → {len(rate_combined)} rate flags "
                f"(mismatches={len(rate_result)}, "
                f"overage={len(overage_result)}, "
                f"discounts={len(discount_result)})")

    # ── 3. Roaming Anomalies ──────────────────────────────────────
    logger.info("Engine 3/5: Roaming Anomaly Check")
    roam_result = pd.DataFrame()
    roam_entitlement_result = pd.DataFrame()
    try:
        roam_result = detect_roaming_anomalies(df, contract, audit=audit)
        roam_entitlement_result = check_roaming_entitlement(df, contract, audit=audit)
        roam_parts = [r for r in [roam_result, roam_entitlement_result]
                      if not r.empty]
        if roam_parts:
            roam_combined = pd.concat(roam_parts, ignore_index=True)
        else:
            roam_combined = pd.DataFrame()
    except Exception as exc:
        logger.error(f"Roaming detection failed: {exc}", exc_info=True)
        roam_combined = pd.DataFrame()
    logger.info(f"  → {len(roam_combined)} roaming flags "
                f"(rate={len(roam_result)}, "
                f"entitlement={len(roam_entitlement_result)})")

    # ── 4. Legacy Rollbacks ───────────────────────────────────────
    logger.info("Engine 4/5: Legacy Rollback Scanner")
    try:
        legacy_result = detect_legacy_rollbacks(
            df, contract, rack_rates=rack_rates, audit=audit
        )
    except Exception as exc:
        logger.error(f"Legacy rollback detection failed: {exc}", exc_info=True)
        legacy_result = pd.DataFrame()
    logger.info(f"  → {len(legacy_result)} legacy rollback flags")

    # ── 5. Duplicates ─────────────────────────────────────────────
    logger.info("Engine 5/5: Duplicate Service Filter")
    try:
        dupe_result = detect_duplicate_services(df, audit=audit)
    except Exception as exc:
        logger.error(f"Duplicate detection failed: {exc}", exc_info=True)
        dupe_result = pd.DataFrame()
    logger.info(f"  → {len(dupe_result)} duplicate flags")

    # ── Filter by minimum confidence ──────────────────────────────
    min_confidence = config.GHOST_MIN_CONFIDENCE
    ghost_result = _filter_by_confidence(ghost_result, min_confidence, "ghost_lines")
    rate_combined = _filter_by_confidence(rate_combined, min_confidence, "rate_mismatches")
    roam_combined = _filter_by_confidence(roam_combined, min_confidence, "roaming")
    legacy_result = _filter_by_confidence(legacy_result, min_confidence, "legacy_rollbacks")
    dupe_result = _filter_by_confidence(dupe_result, min_confidence, "duplicates")

    # ── Calculate totals ──────────────────────────────────────────
    monthly_breakdown = {}
    monthly_breakdown["ghost_lines"] = float(
        ghost_result["estimated_monthly_overcharge"].sum()
        if not ghost_result.empty and "estimated_monthly_overcharge" in ghost_result.columns
        else 0.0
    )
    monthly_breakdown["rate_mismatches"] = float(
        rate_combined["variance_amount"].sum()
        if not rate_combined.empty and "variance_amount" in rate_combined.columns
        else 0.0
    )
    monthly_breakdown["roaming"] = float(
        roam_combined["estimated_overcharge"].sum()
        if not roam_combined.empty and "estimated_overcharge" in roam_combined.columns
        else 0.0
    )
    monthly_breakdown["legacy_rollbacks"] = float(
        legacy_result["estimated_monthly_overcharge"].sum()
        if not legacy_result.empty and "estimated_monthly_overcharge" in legacy_result.columns
        else 0.0
    )
    monthly_breakdown["duplicates"] = float(
        dupe_result["charge_amount"].sum()
        if not dupe_result.empty and "charge_amount" in dupe_result.columns
        else 0.0
    )

    total_monthly_overcharge = sum(monthly_breakdown.values())
    total_annualised = total_monthly_overcharge * 12

    summary = _build_summary(
        {
            "ghost_lines": len(ghost_result),
            "rate_mismatches": len(rate_combined),
            "roaming": len(roam_combined),
            "legacy_rollbacks": len(legacy_result),
            "duplicates": len(dupe_result),
        },
        total_monthly_overcharge,
        monthly_breakdown,
        total_annualised,
    )

    if audit:
        audit.log(
            "detect_runner", "complete",
            f"All engines complete: {summary['total_flags']} total flags, "
            f"${summary['total_monthly_overcharge']:.2f}/month "
            f"(${summary['total_annualised']:.2f}/year)",
            count=summary["total_flags"],
            amount=round(total_monthly_overcharge, 2),
        )

    logger.info("=" * 50)
    logger.info("DETECTION SUMMARY")
    logger.info(f"  Total flags:               {summary['total_flags']}")
    logger.info(f"  Ghost lines:               {summary['breakdown']['ghost_lines']}")
    logger.info(f"  Rate mismatches:           {summary['breakdown']['rate_mismatches']}")
    logger.info(f"  Roaming anomalies:         {summary['breakdown']['roaming']}")
    logger.info(f"  Legacy rollbacks:          {summary['breakdown']['legacy_rollbacks']}")
    logger.info(f"  Duplicates:                {summary['breakdown']['duplicates']}")
    logger.info(f"  Monthly overcharge:        ${total_monthly_overcharge:.2f}")
    logger.info(f"  Annualised overcharge:     ${total_annualised:.2f}")
    logger.info("=" * 50)

    return {
        "ghost_lines": ghost_result,
        "rate_mismatches": rate_combined,
        "roaming": roam_combined,
        "legacy_rollbacks": legacy_result,
        "duplicates": dupe_result,
        "summary": summary,
    }


def _filter_by_confidence(
    df: pd.DataFrame,
    min_confidence: float,
    engine_name: str,
) -> pd.DataFrame:
    """Filter a results DataFrame by minimum confidence threshold."""
    if df.empty:
        return df

    if "confidence" not in df.columns:
        return df

    before = len(df)
    df_filtered = df[df["confidence"] >= min_confidence].copy()
    after = len(df_filtered)
    removed = before - after

    if removed > 0:
        logger.debug(
            f"{engine_name}: filtered {removed} rows below "
            f"confidence threshold {min_confidence}"
        )

    return df_filtered


def _build_summary(
    breakdown: dict[str, int],
    total_monthly: float,
    monthly_breakdown: Optional[dict[str, float]] = None,
    total_annualised: Optional[float] = None,
) -> dict:
    """Build the summary dict."""
    total_flags = sum(breakdown.values())
    if total_annualised is None:
        total_annualised = total_monthly * 12
    if monthly_breakdown is None:
        monthly_breakdown = {}

    return {
        "total_flags": total_flags,
        "total_monthly_overcharge": round(total_monthly, 2),
        "total_annualised": round(total_annualised, 2),
        "breakdown": breakdown,
        "monthly_breakdown": monthly_breakdown,
    }
