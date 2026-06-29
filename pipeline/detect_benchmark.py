"""
1st 4 Mobile — Industry Benchmarking Module

Provides industry-specific benchmarks for comparison.
Each benchmark includes:
  - Industry name
  - Average ghost line percentage
  - Average rate overcharge percentage
  - Average plan inefficiency savings
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("1st4pipeline.benchmark")

INDUSTRY_BENCHMARKS = {
    "mining": {
        "display_name": "Mining & Resources",
        "avg_services": 350,
        "ghost_line_pct": 4.1,
        "rate_overcharge_pct": 2.8,
        "plan_optimisation_pct": 3.5,
        "avg_monthly_spend": 45000,
    },
    "logistics": {
        "display_name": "Logistics & Transport",
        "avg_services": 280,
        "ghost_line_pct": 5.3,
        "rate_overcharge_pct": 3.1,
        "plan_optimisation_pct": 4.2,
        "avg_monthly_spend": 32000,
    },
    "construction": {
        "display_name": "Construction & Engineering",
        "avg_services": 200,
        "ghost_line_pct": 3.8,
        "rate_overcharge_pct": 2.5,
        "plan_optimisation_pct": 2.9,
        "avg_monthly_spend": 25000,
    },
    "manufacturing": {
        "display_name": "Manufacturing",
        "avg_services": 180,
        "ghost_line_pct": 3.2,
        "rate_overcharge_pct": 2.2,
        "plan_optimisation_pct": 2.1,
        "avg_monthly_spend": 22000,
    },
    "healthcare": {
        "display_name": "Healthcare & Medical",
        "avg_services": 150,
        "ghost_line_pct": 2.8,
        "rate_overcharge_pct": 1.9,
        "plan_optimisation_pct": 1.8,
        "avg_monthly_spend": 18000,
    },
    "retail": {
        "display_name": "Retail & Hospitality",
        "avg_services": 120,
        "ghost_line_pct": 4.5,
        "rate_overcharge_pct": 3.0,
        "plan_optimisation_pct": 3.8,
        "avg_monthly_spend": 15000,
    },
    "professional_services": {
        "display_name": "Professional Services",
        "avg_services": 100,
        "ghost_line_pct": 2.5,
        "rate_overcharge_pct": 1.8,
        "plan_optimisation_pct": 1.5,
        "avg_monthly_spend": 12000,
    },
}


def get_benchmarks() -> dict[str, Any]:
    return dict(INDUSTRY_BENCHMARKS)


def get_industry(name: str) -> dict[str, Any] | None:
    return INDUSTRY_BENCHMARKS.get(name)


def compare_client(industry: str, client_ghost_pct: float,
                   client_rate_pct: float,
                   client_total_services: int) -> dict[str, Any]:
    """Compare a client's metrics against industry benchmarks."""
    bench = INDUSTRY_BENCHMARKS.get(industry)
    if not bench:
        return {"error": f"Unknown industry: {industry}"}

    ghost_diff = round(client_ghost_pct - bench["ghost_line_pct"], 1)
    rate_diff = round(client_rate_pct - bench["rate_overcharge_pct"], 1)

    return {
        "industry": bench["display_name"],
        "client_ghost_pct": client_ghost_pct,
        "industry_ghost_pct": bench["ghost_line_pct"],
        "ghost_comparison": "below" if ghost_diff < 0 else "above",
        "ghost_diff_pct": abs(ghost_diff),
        "client_rate_pct": client_rate_pct,
        "industry_rate_pct": bench["rate_overcharge_pct"],
        "rate_comparison": "below" if rate_diff < 0 else "above",
        "rate_diff_pct": abs(rate_diff),
    }
