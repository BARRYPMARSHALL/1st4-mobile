"""
1st 4 Mobile — Rate Plan Validator

Compares billed charges against contracted rates and validates:
  - Monthly access fees against contracted plan fees
  - Overage rates against contracted overage rate
  - Missing volume discounts on invoices
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np

import pipeline.config as config
from pipeline.contract_matrix import ContractMatrix
from pipeline.utils.logging_utils import AuditLogger

logger = logging.getLogger("1st4pipeline.detect_rate")


def detect_rate_mismatches(
    df: pd.DataFrame,
    contract: ContractMatrix,
    audit: Optional[AuditLogger] = None,
) -> pd.DataFrame:
    """Compare monthly_access charges against contracted fees.

    Flags:
      - Unknown plan codes (not in contract matrix)
      - Billed rate differs from contracted fee beyond tolerance

    Args:
        df: Normalised invoice DataFrame.
        contract: ContractMatrix with plan lookups.
        audit: Optional AuditLogger.

    Returns:
        DataFrame with rate mismatch flags.
    """
    rows: list[dict] = []

    if df.empty:
        logger.warning("detect_rate_mismatches called with empty DataFrame")
        return _empty_result()

    logger.info(f"Running rate mismatch detection on {len(df)} rows")

    # Filter to monthly_access charges
    access_df = df[df["charge_category"] == "monthly_access"].copy()
    if access_df.empty:
        logger.info("No monthly_access charges found for rate validation")
        return _empty_result()

    tolerance_pct = config.RATE_TOLERANCE_PCT
    tolerance_fixed = config.RATE_TOLERANCE_FIXED

    for _, row in access_df.iterrows():
        sid = row.get("service_id")
        plan_code = row.get("plan_code")
        billed_amount = float(row.get("charge_amount") or 0)

        plan_code_str = str(plan_code) if pd.notna(plan_code) else ""

        if not plan_code_str:
            rows.append({
                "service_id": sid,
                "plan_code": "",
                "detection_method": "missing_plan_code",
                "confidence": 0.70,
                "billed_amount": billed_amount,
                "contracted_amount": None,
                "variance_amount": billed_amount,
                "variance_pct": 100.0,
                "detail": "No plan code available for this service",
            })
            continue

        plan = contract.get_plan(plan_code_str)
        if plan is None:
            # Unknown plan code
            rows.append({
                "service_id": sid,
                "plan_code": plan_code_str,
                "detection_method": "unknown_plan_code",
                "confidence": 0.70,
                "billed_amount": billed_amount,
                "contracted_amount": None,
                "variance_amount": billed_amount,
                "variance_pct": 100.0,
                "detail": f"Plan code '{plan_code_str}' not found in contract matrix",
            })
            continue

        contracted_fee = contract.get_contracted_monthly_fee(
            plan_code_str, apply_discounts=True
        )
        if contracted_fee is None:
            # Plan exists but has no monthly_access_fee defined
            continue

        variance = billed_amount - contracted_fee
        variance_pct = (
            (abs(variance) / contracted_fee * 100.0)
            if contracted_fee != 0
            else 100.0
        )

        allowed_variance = max(
            contracted_fee * tolerance_pct,
            tolerance_fixed,
        )

        if abs(variance) > allowed_variance:
            # Determine confidence based on variance magnitude
            severity_ratio = abs(variance) / max(allowed_variance, 0.01)
            confidence = min(0.95, 0.70 + (severity_ratio * 0.05))

            rows.append({
                "service_id": sid,
                "plan_code": plan_code_str,
                "detection_method": "rate_mismatch",
                "confidence": round(confidence, 2),
                "billed_amount": round(billed_amount, 2),
                "contracted_amount": round(contracted_fee, 2),
                "variance_amount": round(variance, 2),
                "variance_pct": round(variance_pct, 2),
                "detail": (
                    f"Plan '{plan_code_str}': billed ${billed_amount:.2f} vs "
                    f"contracted ${contracted_fee:.2f} "
                    f"(variance ${variance:+.2f} / {variance_pct:.1f}%, "
                    f"tolerance {tolerance_pct*100:.0f}%+${tolerance_fixed:.2f})"
                ),
            })

    result = pd.DataFrame(rows)
    if not result.empty:
        result = _reorder_columns(result)

    if audit:
        audit.log(
            "rate_detect", "rate_mismatches",
            f"Found {len(result)} rate mismatches",
            count=len(result),
        )

    logger.info(f"Rate mismatches detected: {len(result)}")
    return result


def validate_overage_rates(
    df: pd.DataFrame,
    contract: ContractMatrix,
    audit: Optional[AuditLogger] = None,
) -> pd.DataFrame:
    """Check overage charges against contracted overage rates.

    Compares the billed_rate (per-MB/GB) for overage charges against
    the contracted overage_rate from the plan definition.

    Args:
        df: Normalised invoice DataFrame.
        contract: ContractMatrix with plan lookups.
        audit: Optional AuditLogger.

    Returns:
        DataFrame with overage rate flags.
    """
    rows: list[dict] = []

    if df.empty:
        return _empty_result()

    # Filter to overage charges
    overage_df = df[df["charge_category"] == "overage"].copy()
    if overage_df.empty:
        logger.info("No overage charges found for validation")
        return _empty_result()

    tolerance_pct = config.OVERAGE_TOLERANCE_PCT
    logger.info(f"Validating {len(overage_df)} overage rows (tolerance={tolerance_pct*100:.0f}%)")

    for _, row in overage_df.iterrows():
        sid = row.get("service_id")
        plan_code = row.get("plan_code")
        billed_rate = float(row.get("billed_rate") or 0)
        billed_amount = float(row.get("charge_amount") or 0)
        usage = float(row.get("usage_units") or 0)

        plan_code_str = str(plan_code) if pd.notna(plan_code) else ""

        if not plan_code_str:
            continue

        contracted_rate = contract.get_overage_rate(plan_code_str)
        if contracted_rate is None:
            # Plan exists but has no overage rate defined — not an error
            continue

        if billed_rate <= 0:
            # No billed rate to compare
            continue

        variance_pct = abs(billed_rate - contracted_rate) / contracted_rate * 100.0

        if variance_pct > tolerance_pct * 100.0:
            overcharge = (billed_rate - contracted_rate) * usage if usage > 0 else 0.0
            rows.append({
                "service_id": sid,
                "plan_code": plan_code_str,
                "detection_method": "overage_rate_mismatch",
                "confidence": 0.85,
                "billed_amount": round(billed_amount, 2),
                "contracted_amount": round(contracted_rate, 2),
                "variance_amount": round(billed_rate - contracted_rate, 4),
                "variance_pct": round(variance_pct, 2),
                "billed_rate": round(billed_rate, 4),
                "contracted_rate": round(contracted_rate, 4),
                "usage_units": round(usage, 2),
                "estimated_overcharge": round(max(overcharge, 0.0), 2),
                "detail": (
                    f"Overage rate mismatch on plan '{plan_code_str}': "
                    f"billed ${billed_rate:.4f}/unit vs "
                    f"contracted ${contracted_rate:.4f}/unit "
                    f"({variance_pct:.1f}% variance)"
                ),
            })

    result = pd.DataFrame(rows)
    if not result.empty:
        result = _reorder_columns(result)

    if audit:
        audit.log(
            "rate_detect", "overage_rates",
            f"Found {len(result)} overage rate mismatches",
            count=len(result),
        )

    logger.info(f"Overage rate mismatches: {len(result)}")
    return result


def validate_discounts(
    df: pd.DataFrame,
    contract: ContractMatrix,
    audit: Optional[AuditLogger] = None,
) -> pd.DataFrame:
    """Check for missing volume discounts on the invoice.

    Looks for services whose plan has applicable discounts in the contract
    but the billed amount matches the undiscounted fee (suggesting the
    discount was not applied on the invoice).

    Args:
        df: Normalised invoice DataFrame.
        contract: ContractMatrix with discount definitions.
        audit: Optional AuditLogger.

    Returns:
        DataFrame with missing discount flags.
    """
    rows: list[dict] = []

    if df.empty:
        return _empty_result()

    # Get all discount configurations
    # We check if the discount section exists in the contract data
    discount_list = contract._data.get("discounts", []) if hasattr(contract, "_data") else []
    if not discount_list:
        logger.info("No discounts defined in contract — skipping discount validation")
        return _empty_result()

    # Filter to monthly_access charges with a known plan
    access_df = df[
        (df["charge_category"] == "monthly_access")
        & (df["plan_code"].notna())
    ].copy()

    if access_df.empty:
        logger.info("No monthly_access charges with plan codes for discount validation")
        return _empty_result()

    logger.info(
        f"Validating discounts across {len(access_df)} monthly_access rows "
        f"({len(discount_list)} discounts defined)"
    )

    for _, row in access_df.iterrows():
        sid = row.get("service_id")
        plan_code = str(row.get("plan_code", ""))
        billed_amount = float(row.get("charge_amount") or 0)

        if not plan_code:
            continue

        # Get contracted monthly fee without discounts
        fee_no_discounts = contract.get_contracted_monthly_fee(
            plan_code, apply_discounts=False
        )
        fee_with_discounts = contract.get_contracted_monthly_fee(
            plan_code, apply_discounts=True
        )

        if fee_no_discounts is None or fee_with_discounts is None:
            continue

        discount_amount = fee_no_discounts - fee_with_discounts
        if discount_amount <= 0:
            # No applicable discounts for this plan
            continue

        # Check if the billed amount is close to the undiscounted fee
        # (within tolerance), meaning the discount was likely not applied
        diff_no_discount = abs(billed_amount - fee_no_discounts)
        diff_with_discount = abs(billed_amount - fee_with_discounts)

        tol = max(fee_no_discounts * config.RATE_TOLERANCE_PCT, config.RATE_TOLERANCE_FIXED)

        if diff_no_discount <= tol and diff_with_discount > tol:
            # Billed at undiscounted rate — discount not applied
            rows.append({
                "service_id": sid,
                "plan_code": plan_code,
                "detection_method": "missing_discount",
                "confidence": 0.80,
                "billed_amount": round(billed_amount, 2),
                "contracted_amount": round(fee_with_discounts, 2),
                "variance_amount": round(billed_amount - fee_with_discounts, 2),
                "variance_pct": round(
                    (billed_amount - fee_with_discounts) / fee_with_discounts * 100.0
                    if fee_with_discounts != 0
                    else 100.0,
                    2,
                ),
                "detail": (
                    f"Plan '{plan_code}' billed ${billed_amount:.2f} "
                    f"(undiscounted rate ${fee_no_discounts:.2f}) — "
                    f"discount of ${discount_amount:.2f} not applied. "
                    f"Expected discounted fee: ${fee_with_discounts:.2f}"
                ),
            })

    result = pd.DataFrame(rows)
    if not result.empty:
        result = _reorder_columns(result)

    if audit:
        audit.log(
            "rate_detect", "missing_discounts",
            f"Found {len(result)} missing discounts",
            count=len(result),
        )

    logger.info(f"Missing discounts detected: {len(result)}")
    return result


def _empty_result() -> pd.DataFrame:
    """Return an empty result DataFrame with standard columns."""
    return pd.DataFrame(columns=[
        "service_id", "plan_code", "detection_method", "confidence",
        "billed_amount", "contracted_amount", "variance_amount",
        "variance_pct", "detail",
    ])


def _reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure consistent column order for result DataFrames."""
    order = [
        "service_id", "plan_code", "detection_method", "confidence",
        "billed_amount", "contracted_amount", "variance_amount",
        "variance_pct", "detail",
    ]
    # Keep any extra columns (like billed_rate, usage_units) at the end
    extra = [c for c in df.columns if c not in order]
    return df[[c for c in order if c in df.columns] + extra]
