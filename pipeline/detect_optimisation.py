"""
1st 4 Mobile — Contract Optimisation Detection Engine

Identifies services that could be on cheaper plans based on actual usage.
Generates additional savings beyond error recovery.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("1st4pipeline.optimisation")


# Typical Australian business mobile plans (2026)
PLAN_LIBRARY = {
    "telstra_business_basic": {"monthly": 45, "data_gb": 5, "voice_mins": 200},
    "telstra_business_standard": {"monthly": 65, "data_gb": 20, "voice_mins": 500},
    "telstra_business_premium": {"monthly": 95, "data_gb": 50, "voice_mins": 1000},
    "telstra_business_ultimate": {"monthly": 135, "data_gb": 150, "voice_mins": 2000},
    "optus_business_basic": {"monthly": 40, "data_gb": 5, "voice_mins": 200},
    "optus_business_standard": {"monthly": 60, "data_gb": 20, "voice_mins": 500},
    "optus_business_premium": {"monthly": 90, "data_gb": 50, "voice_mins": 1000},
    "optus_business_ultimate": {"monthly": 120, "data_gb": 100, "voice_mins": 2000},
}


class OptimisationDetector:
    """Detect services that could be cheaper on a different plan."""

    def detect(self, normalised: list[dict[str, Any]],
               contract_matrix=None) -> list[dict[str, Any]]:
        """Analyse each service's usage and recommend plan changes."""
        findings = []

        for record in normalised:
            service_id = record.get("service_id", "")
            plan_name = record.get("plan_name", "")
            carrier = self._detect_carrier(plan_name)

            # Estimate usage from the record
            data_used = self._parse_gb(record.get("data_used", 0))
            voice_used = self._parse_mins(record.get("voice_used", 0))

            if not carrier:
                continue

            current_plan = self._find_plan(plan_name, carrier)
            if not current_plan:
                continue

            # Find the cheapest plan that covers this usage
            best_plan, best_price = self._find_best_plan(
                carrier, data_used, voice_used
            )

            if best_plan and best_price < current_plan["monthly"]:
                savings = current_plan["monthly"] - best_price
                if savings >= 10:  # Only flag if savings > $10/month
                    findings.append({
                        "type": "plan_optimisation",
                        "service_id": service_id,
                        "current_plan": plan_name,
                        "recommended_plan": best_plan,
                        "current_monthly": current_plan["monthly"],
                        "recommended_monthly": best_price,
                        "monthly_savings": round(savings, 2),
                        "data_used_gb": round(data_used, 2),
                        "voice_used_mins": voice_used,
                    })

        return findings

    def get_total_savings(self, findings: list[dict]) -> float:
        return sum(f.get("monthly_savings", 0) for f in findings)

    def _parse_cost(self, val) -> float:
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    def _parse_gb(self, val) -> float:
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    def _parse_mins(self, val) -> float:
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0

    def _detect_carrier(self, plan_name: str) -> str | None:
        name_lower = plan_name.lower()
        if "telstra" in name_lower:
            return "telstra"
        if "optus" in name_lower:
            return "optus"
        return None

    def _find_plan(self, plan_name: str, carrier: str) -> dict | None:
        name_lower = plan_name.lower().replace(" ", "_")
        for key, plan in PLAN_LIBRARY.items():
            if carrier in key and key.endswith(name_lower.split("_")[-1]):
                return plan
        # Return the most expensive plan as default (conservative)
        carrier_plans = {
            k: v for k, v in PLAN_LIBRARY.items() if k.startswith(carrier)
        }
        if carrier_plans:
            return max(carrier_plans.values(), key=lambda p: p["monthly"])
        return None

    def _find_best_plan(self, carrier: str, data_gb: float,
                        voice_mins: int) -> tuple[str | None, float]:
        carrier_plans = {
            k: v for k, v in PLAN_LIBRARY.items() if k.startswith(carrier)
        }
        candidates = []
        for key, plan in carrier_plans.items():
            data_match = plan["data_gb"] >= data_gb
            voice_match = plan["voice_mins"] >= voice_mins
            if data_match and voice_match:
                candidates.append((key, plan["monthly"]))

        if not candidates:
            return None, 0.0

        candidates.sort(key=lambda x: x[1])
        return candidates[0]
