"""
1st 4 Mobile — Contract Matrix Loader & Lookup

Loads a telecom contract matrix from a YAML file and provides
lookup methods for plans, rates, discounts, and roaming charges.

Supports wildcard '*' in discount applies_to fields.
"""

import logging
from pathlib import Path
from typing import Optional

import yaml

from pipeline.config import CONTRACTS_DIR

logger = logging.getLogger("1st4pipeline.contract_matrix")

# Required top-level keys in a valid contract YAML
REQUIRED_CONTRACT_KEYS = {"client", "contract", "rate_plans"}

# Required fields per rate plan
REQUIRED_PLAN_FIELDS = {"plan_code", "plan_name", "service_type",
                        "monthly_access_fee"}

# Optional fields per rate plan with defaults
OPTIONAL_PLAN_FIELDS = {
    "data_pool": None,
    "voice": None,
    "sms": None,
    "contract_term_months": 12,
    "voice_included": 0,
    "overage_voice_rate": None,
    "overage_rate": None,
}


class ContractMatrix:
    """Telecom contract matrix loader and lookup service.

    Loads a contract YAML file and provides query methods for plan
    details, rates, discounts, and roaming charges.

    Usage:
        cm = ContractMatrix("my_contract.yaml")
        plan = cm.get_plan("MBP-50GB-POOL")
        fee = cm.get_contracted_monthly_fee("MBP-50GB-POOL")
    """

    def __init__(self, contract_path: Optional[str | Path] = None):
        """Initialise by loading a contract YAML file.

        Args:
            contract_path: Path to contract YAML. If None, tries
                to find a contract file in the configured CONTRACTS_DIR.
        """
        self._data: dict = {}
        self._plans_by_code: dict[str, dict] = {}
        self._path: Optional[Path] = None

        if contract_path:
            self.load(str(contract_path))

    # ── Loading / Validation ──────────────────────────────────────

    def load(self, contract_path: str | Path) -> None:
        """Load and validate a contract YAML file.

        Args:
            contract_path: Path to the contract YAML file.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If required keys or fields are missing.
        """
        path = Path(contract_path)

        if not path.exists():
            # Try CONTRACTS_DIR / filename
            alt_path = CONTRACTS_DIR / path.name
            if alt_path.exists():
                path = alt_path
            else:
                raise FileNotFoundError(
                    f"Contract file not found: {contract_path}"
                )

        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)

        if not isinstance(data, dict):
            raise ValueError(
                f"Contract YAML at {path} is empty or not a mapping"
            )

        self._validate(data)
        self._data = data
        self._path = path
        self._build_index()

        logger.info(
            f"Loaded contract '{self.client_name}' from {path.name}: "
            f"{len(self._plans_by_code)} plans, "
            f"{len(data.get('discounts', []))} discounts, "
            f"{len(data.get('roaming_zones', []))} roaming zones"
        )

    def _validate(self, data: dict) -> None:
        """Validate contract structure."""
        missing = REQUIRED_CONTRACT_KEYS - set(data.keys())
        if missing:
            raise ValueError(
                f"Contract missing required keys: {missing}"
            )

        client_info = data.get("client", {})
        if not isinstance(client_info, dict):
            raise ValueError("Contract 'client' section must be a mapping")

        contract_info = data.get("contract", {})
        if not isinstance(contract_info, dict):
            raise ValueError("Contract 'contract' section must be a mapping")

        rate_plans = data.get("rate_plans", [])
        if not isinstance(rate_plans, list):
            raise ValueError("Contract 'rate_plans' must be a list")
        if not rate_plans:
            raise ValueError("Contract must have at least one rate plan")

        for i, plan in enumerate(rate_plans):
            if not isinstance(plan, dict):
                raise ValueError(f"Rate plan at index {i} is not a mapping")
            missing_fields = REQUIRED_PLAN_FIELDS - set(plan.keys())
            if missing_fields:
                raise ValueError(
                    f"Rate plan '{plan.get('plan_code', f'index {i}')}' "
                    f"missing required fields: {missing_fields}"
                )

    def _build_index(self) -> None:
        """Build a fast plan_code → plan dict lookup."""
        self._plans_by_code = {}
        for plan in self._data.get("rate_plans", []):
            code = plan.get("plan_code")
            if code:
                self._plans_by_code[code] = plan

    # ── Properties ────────────────────────────────────────────────

    @property
    def client_name(self) -> str:
        """Get client name from contract."""
        return self._data.get("client", {}).get("name", "Unknown")

    @property
    def effective_date(self) -> Optional[str]:
        """Contract effective date string."""
        return self._data.get("contract", {}).get("effective_date")

    @property
    def expiry_date(self) -> Optional[str]:
        """Contract expiry date string."""
        return self._data.get("contract", {}).get("expiry_date")

    @property
    def account_numbers(self) -> dict:
        """Get account numbers dict {provider: [numbers]}."""
        return self._data.get("client", {}).get("account_numbers", {})

    @property
    def plan_codes(self) -> list[str]:
        """Get list of all plan codes in the contract."""
        return list(self._plans_by_code.keys())

    # ── Plan Lookups ──────────────────────────────────────────────

    def get_plan(self, plan_code: str) -> Optional[dict]:
        """Get a rate plan by its code.

        Args:
            plan_code: Rate plan code (e.g. 'MBP-50GB-POOL').

        Returns:
            Plan dict or None if not found.
        """
        return self._plans_by_code.get(plan_code)

    def get_contracted_monthly_fee(
        self, plan_code: str, apply_discounts: bool = True
    ) -> Optional[float]:
        """Get the contracted monthly access fee for a plan.

        Args:
            plan_code: Rate plan code.
            apply_discounts: If True, apply applicable discounts
                (using default sim_count=1, contract_years=0).

        Returns:
            Monthly fee as float, or None if plan not found.
        """
        plan = self.get_plan(plan_code)
        if plan is None:
            return None

        fee = plan.get("monthly_access_fee")
        if fee is None:
            return None

        fee = float(fee)

        if apply_discounts:
            discounts = self.get_applicable_discounts(
                plan_code, sim_count=1, contract_years=0
            )
            for discount in discounts:
                disc_type = discount.get("type", "")
                value = float(discount.get("value", 0))
                if disc_type == "percentage":
                    fee -= fee * (value / 100.0)
                elif disc_type == "fixed":
                    fee -= value

        return round(fee, 2)

    def get_overage_rate(self, plan_code: str) -> Optional[float]:
        """Get the data overage rate for a plan.

        Checks 'overage_rate' field first, then inside 'data_pool'.

        Args:
            plan_code: Rate plan code.

        Returns:
            Overage rate per MB/GB as float, or None.
        """
        plan = self.get_plan(plan_code)
        if plan is None:
            return None

        # Check top-level overage_rate
        rate = plan.get("overage_rate")
        if rate is not None:
            return float(rate)

        # Check inside data_pool
        data_pool = plan.get("data_pool", {})
        if isinstance(data_pool, dict):
            rate = data_pool.get("overage_rate")
            if rate is not None:
                return float(rate)

        return None

    def get_roaming_rate(
        self, zone_name: str, charge_type: str
    ) -> Optional[float]:
        """Get a roaming rate for a specific zone and charge type.

        Args:
            zone_name: Zone name string (fuzzy-matched).
            charge_type: One of 'data', 'voice', 'sms' (or
                'data_rate', 'voice_rate', 'sms_rate').

        Returns:
            Rate as float per unit (MB/min/SMS), or None.
        """
        zones = self._data.get("roaming_zones", [])
        if not zones:
            return None

        # Normalise charge_type
        ct_key = charge_type.lower().replace(" ", "_")
        if not ct_key.endswith("_rate"):
            ct_key = f"{ct_key}_rate"

        # Fuzzy-zone matching: find best match
        best_zone = None
        best_score = 0
        zn_lower = zone_name.lower()

        for zone in zones:
            z_name = str(zone.get("zone", ""))
            z_name_lower = z_name.lower()

            # Exact match
            if zn_lower == z_name_lower:
                best_zone = zone
                break

            # Substring match (zone name may contain the input)
            if zn_lower in z_name_lower or z_name_lower in zn_lower:
                # Score by length of match
                match_len = len(set(zn_lower.split()) & set(z_name_lower.split()))
                if match_len > best_score:
                    best_score = match_len
                    best_zone = zone

        if best_zone is None:
            return None

        rate = best_zone.get(ct_key)
        if rate is not None:
            return float(rate)

        # Try without _rate suffix
        rate = best_zone.get(charge_type.lower().strip())
        if rate is not None:
            return float(rate)

        return None

    def get_applicable_discounts(
        self, plan_code: str, sim_count: int = 1,
        contract_years: int = 0
    ) -> list[dict]:
        """Get all discounts applicable to a plan.

        Supports wildcard '*' in discount applies_to, meaning the
        discount applies to all plans.

        Args:
            plan_code: Rate plan code to check.
            sim_count: Number of SIMs (for volume condition checks).
            contract_years: Contract tenure in years (for loyalty checks).

        Returns:
            List of discount dicts applicable to the plan.
        """
        discounts = self._data.get("discounts", [])
        if not discounts:
            return []

        applicable: list[dict] = []

        for discount in discounts:
            applies_to = discount.get("applies_to", [])

            # Check if this plan is in the applies_to list
            plan_matched = False
            for target in applies_to:
                if target == "*":
                    plan_matched = True
                    break
                if target == plan_code:
                    plan_matched = True
                    break

            if not plan_matched:
                continue

            # Check conditions
            condition = discount.get("condition", "")
            if condition:
                if not self._check_condition(condition, sim_count, contract_years):
                    continue

            applicable.append(discount)

        return applicable

    # ── Condition Evaluation ──────────────────────────────────────

    @staticmethod
    def _check_condition(condition: str, sim_count: int,
                         contract_years: int) -> bool:
        """Evaluate a simple discount condition string.

        Supports conditions like:
        - "total_sims >= 250"
        - "contract_years >= 3"
        - "total_sims > 100 and contract_years >= 2"

        Args:
            condition: Condition string.
            sim_count: Current SIM count.
            contract_years: Current contract tenure.

        Returns:
            True if condition is met.
        """
        # Build a safe evaluation context
        context = {
            "total_sims": sim_count,
            "sim_count": sim_count,
            "contract_years": contract_years,
            "tenure_years": contract_years,
        }

        try:
            # Replace logical operators for safety
            expr = condition.strip()
            # Only allow known variable names and safe operators
            allowed = set(context.keys()) | {
                ">=", "<=", ">", "<", "==", "!=", "and", "or",
                "(", ")", "0", "1", "2", "3", "4", "5", "6", "7",
                "8", "9", ".", " ", "+", "-",
            }
            # Quick safety check: ensure only safe tokens
            import re
            tokens = re.split(r"(\b\w+\b|[<>=!]+|\d+\.?\d*)", expr)
            for token in tokens:
                token = token.strip()
                if not token:
                    continue
                if token in ("and", "or"):
                    continue
                if re.match(r"^\d+\.?\d*$", token):
                    continue
                if token in allowed:
                    continue
                # Unknown token - condition might be unsafe
                logger.warning(f"Unknown token in condition '{condition}': {token}")
                return False

            result = eval(expr, {"__builtins__": {}}, context)
            return bool(result)
        except Exception as exc:
            logger.warning(
                f"Failed to evaluate condition '{condition}': {exc}"
            )
            # Default to not applicable if we can't evaluate
            return False

    # ── Pool Lookups ──────────────────────────────────────────────

    def get_pool_config(self, pool_id: str = None) -> list[dict]:
        """Get pool configuration(s).

        Args:
            pool_id: Optional pool ID to filter by.

        Returns:
            List of pool config dicts.
        """
        pools = self._data.get("pool_configuration", [])
        if not pools:
            return []

        if pool_id:
            return [p for p in pools if p.get("pool_id") == pool_id]
        return pools

    # ── Utility ───────────────────────────────────────────────────

    def __repr__(self) -> str:
        path_str = str(self._path) if self._path else "not loaded"
        return (
            f"<ContractMatrix client='{self.client_name}' "
            f"plans={len(self._plans_by_code)} "
            f"path={path_str}>"
        )


# ── Module-level convenience ─────────────────────────────────────


def load_contract(contract_path: str | Path) -> ContractMatrix:
    """Load a contract matrix from a YAML file (convenience wrapper).

    Args:
        contract_path: Path to contract YAML.

    Returns:
        ContractMatrix instance.
    """
    return ContractMatrix(contract_path)
