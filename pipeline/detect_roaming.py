"""
1st 4 Mobile — Roaming Anomaly Check

Detects roaming charge anomalies by:
  1. Classifying roaming zone from charge descriptions
  2. Comparing billed rates against contracted roaming rates
  3. Flagging roaming charges on plans without roaming entitlement
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np

import pipeline.config as config
from pipeline.contract_matrix import ContractMatrix
from pipeline.utils.logging_utils import AuditLogger
from pipeline.utils.text_utils import extract_charge_type_from_description

logger = logging.getLogger("1st4pipeline.detect_roaming")

# Keywords maps for classifying roaming zones from descriptions
_ZONE_1_KEYWORDS = [
    "zone 1", "zone1", "nz", "new zealand", "usa", "canada",
    "uk", "united kingdom", "western europe", "europe zone 1",
]
_ZONE_2_KEYWORDS = [
    "zone 2", "zone2", "europe", "asia", "japan", "hong kong",
    "singapore", "south korea", "china", "india",
]
_ZONE_3_KEYWORDS = [
    "zone 3", "zone3", "rest of world", "international", "other",
    "global", "worldwide",
]


def classify_roaming_zone(description: str) -> str:
    """Classify a roaming charge description into a zone.

    Uses keyword matching against known zone definitions. Returns
    'Zone 1', 'Zone 2', 'Zone 3', or 'Unknown'.

    When uncertain, defaults to 'Zone 3' (most expensive) to err
    on the side of flagging overcharges.

    Args:
        description: Charge description string.

    Returns:
        Zone name string.
    """
    if not description:
        return "Zone 3"  # default when uncertain

    desc_lower = description.lower().strip()

    # Check for explicit zone mentions first
    for zone_kw in _ZONE_1_KEYWORDS:
        if zone_kw in desc_lower:
            return "Zone 1"
    for zone_kw in _ZONE_2_KEYWORDS:
        if zone_kw in desc_lower:
            return "Zone 2"
    for zone_kw in _ZONE_3_KEYWORDS:
        if zone_kw in desc_lower:
            return "Zone 3"

    # If 'roam' or 'inter' is in description but no zone match, default Zone 3
    if "roam" in desc_lower or "inter" in desc_lower:
        return "Zone 3"

    return "Zone 3"  # default most expensive when uncertain


def detect_roaming_anomalies(
    df: pd.DataFrame,
    contract: ContractMatrix,
    audit: Optional[AuditLogger] = None,
) -> pd.DataFrame:
    """Detect roaming charges where billed rate exceeds contracted rate.

    Compares the billed rate per unit against the contracted roaming rate
    for the classified zone and charge type.

    Args:
        df: Normalised invoice DataFrame.
        contract: ContractMatrix with roaming zone rates.
        audit: Optional AuditLogger.

    Returns:
        DataFrame with roaming anomaly flags.
    """
    rows: list[dict] = []

    if df.empty:
        logger.warning("detect_roaming_anomalies called with empty DataFrame")
        return _empty_result()

    # Filter to roaming charges
    roam_df = df[df["charge_category"] == "roaming"].copy()
    if roam_df.empty:
        logger.info("No roaming charges found for anomaly detection")
        return _empty_result()

    tolerance_pct = config.ROAMING_TOLERANCE_PCT
    logger.info(
        f"Checking {len(roam_df)} roaming charges (tolerance={tolerance_pct*100:.0f}%)"
    )

    for _, row in roam_df.iterrows():
        sid = row.get("service_id")
        plan_code = row.get("plan_code")
        description = str(row.get("charge_description") or "")
        billed_amount = float(row.get("charge_amount") or 0)
        billed_rate = float(row.get("billed_rate") or 0)
        usage = float(row.get("usage_units") or 0)

        if billed_rate <= 0:
            # Try to derive rate from amount / usage
            if usage > 0:
                billed_rate = billed_amount / usage

        if billed_rate <= 0:
            continue

        plan_code_str = str(plan_code) if pd.notna(plan_code) else ""

        # Classify zone
        zone = classify_roaming_zone(description)

        # Determine charge type (data, voice, sms)
        charge_type = extract_charge_type_from_description(description)

        # Get contracted rate
        contracted_rate = contract.get_roaming_rate(zone, charge_type)

        if contracted_rate is None:
            # Contract doesn't define this zone/type — try generic
            contracted_rate = contract.get_roaming_rate(zone, "data")
        if contracted_rate is None:
            contracted_rate = contract.get_roaming_rate("Zone 3", "data")

        if contracted_rate is None or contracted_rate <= 0:
            # No contracted rate to compare against
            continue

        variance_pct = (billed_rate - contracted_rate) / contracted_rate * 100.0

        if variance_pct > tolerance_pct * 100.0:
            overcharge = (billed_rate - contracted_rate) * usage if usage > 0 else 0.0
            rows.append({
                "service_id": sid,
                "plan_code": plan_code_str,
                "detection_method": "roaming_rate_overcharge",
                "confidence": 0.85,
                "zone": zone,
                "charge_type": charge_type,
                "billed_amount": round(billed_amount, 2),
                "contracted_rate": round(contracted_rate, 4),
                "billed_rate": round(billed_rate, 4),
                "variance_pct": round(variance_pct, 2),
                "usage_units": round(usage, 2),
                "estimated_overcharge": round(max(overcharge, 0.0), 2),
                "detail": (
                    f"Roaming {charge_type} charge in {zone}: "
                    f"billed ${billed_rate:.4f}/unit vs "
                    f"contracted ${contracted_rate:.4f}/unit "
                    f"({variance_pct:.1f}% above contracted rate)"
                ),
            })

    result = pd.DataFrame(rows)
    if audit:
        audit.log(
            "roaming_detect", "roaming_anomalies",
            f"Found {len(result)} roaming rate anomalies",
            count=len(result),
        )

    logger.info(f"Roaming rate anomalies detected: {len(result)}")
    return result


def check_roaming_entitlement(
    df: pd.DataFrame,
    contract: ContractMatrix,
    audit: Optional[AuditLogger] = None,
) -> pd.DataFrame:
    """Flag roaming charges on plans that do not include roaming.

    Checks whether the plan definition indicates roaming is included.
    If a plan has no roaming entitlement but has roaming charges,
    those are flagged as billing errors.

    Args:
        df: Normalised invoice DataFrame.
        contract: ContractMatrix with plan definitions.
        audit: Optional AuditLogger.

    Returns:
        DataFrame with roaming entitlement flags.
    """
    rows: list[dict] = []

    if df.empty:
        return _empty_result()

    # Filter to roaming charges
    roam_df = df[df["charge_category"] == "roaming"].copy()
    if roam_df.empty:
        logger.info("No roaming charges found for entitlement check")
        return _empty_result()

    logger.info(f"Checking roaming entitlement for {len(roam_df)} roaming charges")

    for _, row in roam_df.iterrows():
        sid = row.get("service_id")
        plan_code = row.get("plan_code")
        description = str(row.get("charge_description") or "")
        billed_amount = float(row.get("charge_amount") or 0)

        plan_code_str = str(plan_code) if pd.notna(plan_code) else ""

        if not plan_code_str:
            continue

        plan = contract.get_plan(plan_code_str)
        if plan is None:
            continue

        # Check if the plan has roaming defined
        # Plans with roaming may have 'roaming_included' or a 'roaming' section
        roaming_included = plan.get("roaming_included", None)
        if roaming_included is True:
            # Roaming is included — skip
            continue

        has_roaming_section = "roaming" in plan or "roaming_zones" in plan
        if roaming_included is False or (roaming_included is None and not has_roaming_section):
            # No roaming entitlement
            zone = classify_roaming_zone(description)
            rows.append({
                "service_id": sid,
                "plan_code": plan_code_str,
                "detection_method": "roaming_not_entitled",
                "confidence": 0.90,
                "zone": zone,
                "billed_amount": round(billed_amount, 2),
                "estimated_overcharge": round(billed_amount, 2),
                "detail": (
                    f"Roaming charge on plan '{plan_code_str}' which "
                    f"does not include roaming entitlement. "
                    f"Charge: '{description}' (${billed_amount:.2f})"
                ),
            })

    result = pd.DataFrame(rows)
    if audit:
        audit.log(
            "roaming_detect", "roaming_entitlement",
            f"Found {len(result)} roaming charges without entitlement",
            count=len(result),
        )

    logger.info(f"Roaming entitlement issues: {len(result)}")
    return result


def _empty_result() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "service_id", "plan_code", "detection_method", "confidence",
        "zone", "charge_type", "billed_amount", "contracted_rate",
        "billed_rate", "variance_pct", "usage_units",
        "estimated_overcharge", "detail",
    ])
