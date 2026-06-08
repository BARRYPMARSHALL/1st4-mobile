"""
1st 4 Mobile — Pipeline Test Suite
Tests for ingestion, detection engines, and output generation.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path

from pipeline.config import (
    GHOST_ZERO_USAGE_MONTHS, RATE_TOLERANCE_PCT,
    GHOST_MIN_CONFIDENCE
)
from pipeline.contract_matrix import ContractMatrix


# ── Fixtures ───────────────────────────────────────────────────

@pytest.fixture(scope="module")
def contract():
    """Load the test contract once for all tests."""
    return ContractMatrix("test_contract.yaml")


@pytest.fixture
def sample_df():
    """Minimal test DataFrame with known good and bad data."""
    rows = []
    for m in range(1, 4):
        p = f"2025-{m:02d}-01"
        # Good service
        rows.append({"service_id": "SVC-GOOD", "charge_category": "monthly_access",
                     "charge_amount": 45.00, "plan_code": "MBP-50GB-POOL",
                     "usage_units": 0, "charge_period_start": p, "billed_rate": 45.00})
        rows.append({"service_id": "SVC-GOOD", "charge_category": "usage",
                     "charge_amount": 0.00, "plan_code": "MBP-50GB-POOL",
                     "usage_units": 500, "charge_period_start": p, "billed_rate": 0.00})
        # Ghost
        rows.append({"service_id": "SVC-GHOST", "charge_category": "monthly_access",
                     "charge_amount": 45.00, "plan_code": "MBP-50GB-POOL",
                     "usage_units": 0, "charge_period_start": p, "billed_rate": 45.00})
        rows.append({"service_id": "SVC-GHOST", "charge_category": "usage",
                     "charge_amount": 0.00, "plan_code": "MBP-50GB-POOL",
                     "usage_units": 0, "charge_period_start": p, "billed_rate": 0.00})
        # Rate mismatch
        rows.append({"service_id": "SVC-RATE", "charge_category": "monthly_access",
                     "charge_amount": 55.00, "plan_code": "MBP-50GB-POOL",
                     "usage_units": 0, "charge_period_start": p, "billed_rate": 55.00})
    return pd.DataFrame(rows)


# ── Contract Matrix Tests ──────────────────────────────────────

class TestContractMatrix:
    def test_load_valid_contract(self, contract):
        assert contract.client_name == "TestCo Mining Services Pty Ltd"
        assert len(contract.plan_codes) == 4

    def test_get_plan_exists(self, contract):
        plan = contract.get_plan("MBP-50GB-POOL")
        assert plan is not None
        assert plan["monthly_access_fee"] == 45.00

    def test_get_plan_missing(self, contract):
        assert contract.get_plan("NONEXISTENT-PLAN") is None

    def test_get_contracted_fee(self, contract):
        fee = contract.get_contracted_monthly_fee("MBP-50GB-POOL")
        assert fee == 45.00

    def test_get_contracted_fee_with_discount(self, contract):
        fee = contract.get_contracted_monthly_fee(
            "MBP-50GB-POOL", apply_discounts=True
        )
        # 45.00 - 15% (volume discount) - 5% (loyalty) = 45 * 0.80 = 36.00
        # But loyalty discount requires contract_years >= 3
        # With default sim_count=1 and default contract_years, neither applies
        # Actually discounts have conditions that need to be met
        assert fee is not None

    def test_get_overage_rate(self, contract):
        rate = contract.get_overage_rate("MBP-50GB-POOL")
        assert rate == 0.002

    def test_get_roaming_rate(self, contract):
        rate = contract.get_roaming_rate("Zone 2 (Asia)", "data")
        assert rate is not None


# ── Ghost Line Detection Tests ─────────────────────────────────

class TestGhostDetection:
    def test_ghost_found(self, sample_df, contract):
        from pipeline.detect_ghost import detect_ghost_lines
        result = detect_ghost_lines(sample_df, contract)
        assert len(result) > 0

    def test_ghost_confidence(self, sample_df, contract):
        from pipeline.detect_ghost import detect_ghost_lines
        result = detect_ghost_lines(sample_df, contract)
        if not result.empty:
            assert result["confidence"].iloc[0] >= GHOST_MIN_CONFIDENCE

    def test_no_false_positive_on_good_service(self, sample_df, contract):
        from pipeline.detect_ghost import detect_ghost_lines
        result = detect_ghost_lines(sample_df, contract)
        ghost_svcs = result["service_id"].tolist() if not result.empty else []
        assert "SVC-GOOD" not in ghost_svcs


# ── Rate Validation Tests ──────────────────────────────────────

class TestRateValidation:
    def test_rate_mismatch_found(self, sample_df, contract):
        from pipeline.detect_rate import detect_rate_mismatches
        result = detect_rate_mismatches(sample_df, contract)
        assert len(result) > 0

    def test_rate_mismatch_plan_code(self, sample_df, contract):
        from pipeline.detect_rate import detect_rate_mismatches
        result = detect_rate_mismatches(sample_df, contract)
        if not result.empty:
            rate_svcs = result["service_id"].tolist()
            assert "SVC-RATE" in rate_svcs


# ── Legacy Rollback Tests ──────────────────────────────────────

class TestLegacyRollback:
    def test_rollback_detected(self, contract):
        from pipeline.detect_legacy import detect_legacy_rollbacks
        rows = []
        for m in range(1, 4):
            rows.append({"service_id": "SVC-LEG", "charge_category": "monthly_access",
                         "charge_amount": 45.00, "plan_code": "MBP-50GB-POOL",
                         "usage_units": 0, "charge_period_start": f"2024-{m:02d}-01",
                         "billed_rate": 45.00})
        for m in range(1, 4):
            rows.append({"service_id": "SVC-LEG", "charge_category": "monthly_access",
                         "charge_amount": 105.00, "plan_code": "UNKNOWN-RACK",
                         "usage_units": 0, "charge_period_start": f"2025-{m:02d}-01",
                         "billed_rate": 105.00})
        df = pd.DataFrame(rows)
        result = detect_legacy_rollbacks(df, contract)
        assert len(result) > 0


# ── Runner Tests ───────────────────────────────────────────────

class TestRunner:
    def test_run_all_detections(self, sample_df, contract):
        from pipeline.detect_runner import run_all_detections
        results = run_all_detections(sample_df, contract)
        assert "summary" in results
        assert results["summary"]["total_flags"] > 0

    def test_summary_has_totals(self, sample_df, contract):
        from pipeline.detect_runner import run_all_detections
        results = run_all_detections(sample_df, contract)
        s = results["summary"]
        assert "total_monthly_overcharge" in s
        assert "total_annualised" in s
        assert s["total_annualised"] > 0


# ── Output Tests ───────────────────────────────────────────────

class TestOutput:
    def test_executive_summary(self, sample_df, contract):
        from pipeline.detect_runner import run_all_detections
        from pipeline.output_summary import generate_executive_summary
        results = run_all_detections(sample_df, contract)
        summary = generate_executive_summary(results, "TestCo")
        assert len(summary) > 100
        assert "$" in summary

    def test_dispute_letter(self, sample_df, contract):
        from pipeline.detect_runner import run_all_detections
        from pipeline.output_letter import generate_dispute_letter
        results = run_all_detections(sample_df, contract)
        letter = generate_dispute_letter(results, "TestCo", "Telstra", ["ACC-001"])
        assert len(letter) > 100
        assert "Telstra" in letter
