"""
1st 4 Mobile — Legacy Rollback Scanner

Detects when services have been silently rolled back to default (rack)
rates — either by plan_code change to an unknown plan, or by price
increases on the same plan beyond the contractual threshold.
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np

import pipeline.config as config
from pipeline.contract_matrix import ContractMatrix
from pipeline.utils.logging_utils import AuditLogger

logger = logging.getLogger("1st4pipeline.detect_legacy")


def detect_legacy_rollbacks(
    df: pd.DataFrame,
    contract: ContractMatrix,
    rack_rates: Optional[dict] = None,
    audit: Optional[AuditLogger] = None,
) -> pd.DataFrame:
    """Detect services that may have rolled back to legacy rack rates.

    Two signals:
      1. Plan code changes to a plan NOT in the contract matrix → possible
         rack rate rollback.
      2. Same plan code but price increases > ROLLBACK_PRICE_INCREASE_PCT
         → possible rate change.

    When rack_rates data is provided, attempts to confirm the rollback by
    matching the new rate against known rack rates.

    Args:
        df: Normalised invoice DataFrame (canonical schema). Must contain
            charge_period_start, plan_code, charge_amount, charge_category,
            and service_id.
        contract: ContractMatrix with contracted plan definitions.
        rack_rates: Optional dict of {plan_code: rate} from rack_rates.yaml.
        audit: Optional AuditLogger.

    Returns:
        DataFrame with legacy rollback flags.
    """
    rows: list[dict] = []

    if df.empty:
        logger.warning("detect_legacy_rollbacks called with empty DataFrame")
        return _empty_result()

    logger.info(f"Running legacy rollback detection on {len(df)} rows")

    min_history_months = config.ROLLBACK_MIN_MONTHS
    price_increase_pct = config.ROLLBACK_PRICE_INCREASE_PCT

    # Focus on monthly_access charges since those reflect plan pricing
    access_df = df[df["charge_category"] == "monthly_access"].copy()
    if access_df.empty:
        logger.info("No monthly_access charges for legacy rollback analysis")
        return _empty_result()

    # Prepare date column and sort
    access_df["_period"] = pd.to_datetime(
        access_df["charge_period_start"], errors="coerce"
    )
    access_df = access_df.dropna(subset=["_period"])
    access_df = access_df.sort_values(["service_id", "_period"])

    # Group by service_id to track changes over time
    grouped = access_df.groupby("service_id")

    for service_id, grp in grouped:
        grp = grp.sort_values("_period").reset_index(drop=True)

        if len(grp) < min_history_months + 1:
            # Not enough history to detect a change
            continue

        # Track plan_code and charge_amount changes
        prev_plan = None
        prev_amount = None
        prev_contracted = None

        for idx, (_, row) in enumerate(grp.iterrows()):
            current_plan = str(row.get("plan_code") or "")
            current_amount = float(row.get("charge_amount") or 0)
            current_period = row["_period"]

            if idx == 0:
                prev_plan = current_plan
                prev_amount = current_amount
                # Get contracted fee for initial plan
                if prev_plan:
                    prev_contracted = contract.get_contracted_monthly_fee(
                        prev_plan, apply_discounts=True
                    )
                continue

            # --- Signal 1: Plan code changed ---
            if current_plan and prev_plan and current_plan != prev_plan:
                # Check if the new plan is in the contract matrix
                new_plan = contract.get_plan(current_plan)
                if new_plan is None:
                    # New plan NOT in contract — possible rack rate rollback
                    overcharge = current_amount - (prev_contracted or prev_amount)
                    confirmed = ""

                    # Try to confirm against rack_rates
                    if rack_rates and current_plan in rack_rates:
                        confirmed = (
                            f" Confirmed by rack_rates: plan '{current_plan}' "
                            f"listed at ${rack_rates[current_plan]:.2f}."
                        )

                    rows.append({
                        "service_id": service_id,
                        "detection_method": "rack_rate_rollback",
                        "confidence": 0.85,
                        "previous_plan": prev_plan,
                        "current_plan": current_plan,
                        "previous_amount": round(prev_amount, 2),
                        "current_amount": round(current_amount, 2),
                        "estimated_monthly_overcharge": round(
                            max(overcharge, 0.0), 2
                        ),
                        "change_date": current_period.date().isoformat(),
                        "detail": (
                            f"Plan changed from '{prev_plan}' "
                            f"(${prev_amount:.2f}) to '{current_plan}' "
                            f"(${current_amount:.2f}) — "
                            f"'{current_plan}' is not in the contract matrix. "
                            f"Possible rack rate rollback.{confirmed}"
                        ),
                    })
                else:
                    # New plan IS in contract — check if price differs from contracted
                    new_contracted = contract.get_contracted_monthly_fee(
                        current_plan, apply_discounts=True
                    )
                    if new_contracted is not None and abs(new_contracted - current_amount) > (
                        max(new_contracted * config.RATE_TOLERANCE_PCT, config.RATE_TOLERANCE_FIXED)
                    ):
                        overcharge = current_amount - new_contracted
                        rows.append({
                            "service_id": service_id,
                            "detection_method": "plan_change_rate_mismatch",
                            "confidence": 0.80,
                            "previous_plan": prev_plan,
                            "current_plan": current_plan,
                            "previous_amount": round(prev_amount, 2),
                            "current_amount": round(current_amount, 2),
                            "estimated_monthly_overcharge": round(
                                max(overcharge, 0.0), 2
                            ),
                            "change_date": current_period.date().isoformat(),
                            "detail": (
                                f"Plan changed from '{prev_plan}' to "
                                f"'{current_plan}': billed ${current_amount:.2f} "
                                f"vs contracted ${new_contracted:.2f} "
                                f"(overcharge ${overcharge:.2f})"
                            ),
                        })

                    # Reset tracking for the new plan
                    prev_plan = current_plan
                    prev_amount = current_amount
                    prev_contracted = new_contracted
                    continue

            # --- Signal 2: Same plan, price increased ---
            if current_plan and current_plan == prev_plan and prev_amount > 0:
                pct_change = (current_amount - prev_amount) / prev_amount * 100.0

                if pct_change > price_increase_pct * 100.0:
                    overcharge = current_amount - prev_amount
                    rack_rate_confirmed = ""

                    # Try to confirm against rack_rates
                    if rack_rates and current_plan in rack_rates:
                        rack_rate = float(rack_rates[current_plan])
                        if abs(current_amount - rack_rate) <= 0.50:
                            rack_rate_confirmed = (
                                f" Confirmed: current rate matches rack rate "
                                f"(${rack_rate:.2f}) for plan '{current_plan}'."
                            )
                        elif abs(prev_amount - rack_rate) <= 0.50:
                            rack_rate_confirmed = (
                                f" Previous rate matched rack rate "
                                f"(${rack_rate:.2f})."
                            )

                    rows.append({
                        "service_id": service_id,
                        "detection_method": "price_increase",
                        "confidence": 0.75,
                        "previous_plan": prev_plan,
                        "current_plan": current_plan,
                        "previous_amount": round(prev_amount, 2),
                        "current_amount": round(current_amount, 2),
                        "estimated_monthly_overcharge": round(
                            max(overcharge, 0.0), 2
                        ),
                        "change_date": current_period.date().isoformat(),
                        "detail": (
                            f"Plan '{current_plan}' price increased from "
                            f"${prev_amount:.2f} to ${current_amount:.2f} "
                            f"({pct_change:.1f}% increase, threshold="
                            f"{price_increase_pct*100:.0f}%).{rack_rate_confirmed}"
                        ),
                    })

            # Update tracking
            prev_plan = current_plan
            prev_amount = current_amount
            if current_plan:
                prev_contracted = contract.get_contracted_monthly_fee(
                    current_plan, apply_discounts=True
                ) or prev_contracted

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("estimated_monthly_overcharge", ascending=False)
        result = result.reset_index(drop=True)
        total_monthly = result["estimated_monthly_overcharge"].sum()
    else:
        total_monthly = 0.0
    total_monthly_val = float(total_monthly) if not isinstance(total_monthly, (int, float)) else total_monthly

    if audit:
        audit.log(
            "legacy_detect", "rollbacks",
            f"Found {len(result)} legacy rollback flags",
            count=len(result),
            amount=round(total_monthly_val, 2),
        )

    logger.info(
        f"Legacy rollbacks detected: {len(result)} flags, "
        f"estimated monthly overcharge=${total_monthly:.2f}"
    )
    return result


def _empty_result() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "service_id", "detection_method", "confidence",
        "previous_plan", "current_plan", "previous_amount",
        "current_amount", "estimated_monthly_overcharge",
        "change_date", "detail",
    ])
