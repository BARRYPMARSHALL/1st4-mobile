"""
1st 4 Mobile — Executive Summary Generation

Generates a concise markdown executive summary of the audit findings
including totals by category, top 3 findings, recovery estimate, fee
estimate, and recommended next steps.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from pipeline.config import OUTPUT_DATE_FORMAT
from pipeline.utils.money_utils import format_currency

logger = logging.getLogger("1st4pipeline.output_summary")


def _extract_top_findings(all_flags: dict, top_n: int = 3) -> list[dict]:
    """Extract the top N highest-value findings across all engines.

    Args:
        all_flags: Result dict from run_all_detections().
        top_n: Number of top findings to extract (default 3).

    Returns:
        List of dicts with keys: category, service_id, amount, description.
    """
    candidates: list[dict] = []

    engine_configs = [
        ("ghost_lines", "Ghost Lines", "estimated_monthly_overcharge", "detail", "service_id"),
        ("rate_mismatches", "Rate Mismatches", "variance_amount", "detail", "service_id"),
        ("roaming", "Roaming Anomalies", "estimated_overcharge", "detail", "service_id"),
        ("legacy_rollbacks", "Legacy Rollbacks", "estimated_monthly_overcharge", "detail", "service_id"),
        ("duplicates", "Duplicates", "charge_amount", "detail", "service_id"),
    ]

    for engine_key, label, amount_col, detail_col, id_col in engine_configs:
        df = all_flags.get(engine_key, pd.DataFrame())
        if df.empty or amount_col not in df.columns:
            continue

        for _, row in df.iterrows():
            amount: float = float(row.get(amount_col, 0) or 0)
            service_id: str = str(row.get(id_col, "Unknown") or "Unknown")
            detail: str = str(row.get(detail_col, "") or "")
            candidates.append({
                "category": label,
                "service_id": service_id,
                "amount": amount,
                "detail": detail[:200],  # truncate
            })

    # Sort by amount descending
    candidates.sort(key=lambda x: x["amount"], reverse=True)

    return candidates[:top_n]


def generate_executive_summary(
    all_flags: dict,
    client_name: str,
    total_recoverable: float = None,
    output_path: str = None,
) -> str:
    """Generate a concise markdown executive summary of audit findings.

    Args:
        all_flags: Result dict from run_all_detections() containing
            DataFrames for each engine and a summary dict.
        client_name: Name of the audited client.
        total_recoverable: Optional override for the recovery estimate.
            If not provided, uses the annualised total from the summary.
        output_path: Optional path to write the markdown file. If not
            provided, the summary is returned as a string.

    Returns:
        The markdown summary as a string. If output_path was provided,
        also writes to that file.

    Raises:
        IOError: If the file cannot be written.
    """
    summary = all_flags.get("summary", {})
    total_flags = int(summary.get("total_flags", 0))
    total_monthly = float(summary.get("total_monthly_overcharge", 0.0))
    total_annualised = float(summary.get("total_annualised", 0.0))

    if total_recoverable is None:
        total_recoverable = total_annualised  # 12 months historical

    fee_estimate = total_recoverable * 0.50  # 50% recovery fee

    breakdown = summary.get("breakdown", {})
    monthly_breakdown = summary.get("monthly_breakdown", {})

    category_labels = {
        "ghost_lines": "Ghost Lines",
        "rate_mismatches": "Rate Mismatches",
        "roaming": "Roaming Anomalies",
        "legacy_rollbacks": "Legacy Rollbacks",
        "duplicates": "Duplicates",
    }

    # Build category table
    table_rows = []
    for key, label in category_labels.items():
        count = breakdown.get(key, 0)
        monthly = monthly_breakdown.get(key, 0.0)
        annualised = monthly * 12.0
        if count > 0 or monthly > 0:
            table_rows.append(
                f"| {label} | {count} | {format_currency(monthly)} | {format_currency(annualised)} |"
            )

    # Top 3 findings
    top_findings = _extract_top_findings(all_flags, top_n=3)

    today_str = datetime.now().strftime(OUTPUT_DATE_FORMAT)

    lines = []
    lines.append(f"# Executive Summary — Billing Audit")
    lines.append(f"")
    lines.append(f"**Client:** {client_name}")
    lines.append(f"**Audit Date:** {today_str}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## Overview")
    lines.append(f"")
    lines.append(
        f"A comprehensive billing audit was conducted for {client_name}. "
        f"The analysis identified **{total_flags} billing irregularities** "
        f"across five detection categories, representing an estimated "
        f"**{format_currency(total_monthly)} per month** "
        f"(**{format_currency(total_annualised)} per year**) in potential overcharges."
    )
    lines.append(f"")

    # ── Totals ────────────────────────────────────────────────────
    lines.append(f"**Total Flags Found:** {total_flags}")
    lines.append(f"**Total Monthly Overcharge:** {format_currency(total_monthly)}")
    lines.append(f"**Total Annualised Overcharge:** {format_currency(total_annualised)}")
    lines.append(f"")

    # ── Breakdown Table ───────────────────────────────────────────
    lines.append(f"## Breakdown by Category")
    lines.append(f"")
    lines.append(f"| Category | Count | Monthly Overcharge | Annualised Overcharge |")
    lines.append(f"|----------|------:|-------------------:|----------------------:|")
    lines.extend(table_rows)
    lines.append(f"| **Total** | **{total_flags}** | **{format_currency(total_monthly)}** | **{format_currency(total_annualised)}** |")
    lines.append(f"")

    # ── Top 3 Findings ────────────────────────────────────────────
    lines.append(f"## Top 3 Findings (Highest Value)")
    lines.append(f"")

    if top_findings:
        for i, finding in enumerate(top_findings, 1):
            lines.append(f"### {i}. [{finding['category']}] {finding['service_id']}")
            lines.append(f"")
            lines.append(f"- **Amount:** {format_currency(finding['amount'])}/mo")
            lines.append(f"- **Detail:** {finding['detail']}")
            lines.append(f"")
    else:
        lines.append(f"No significant findings to report.")
        lines.append(f"")

    # ── Recovery Estimate ─────────────────────────────────────────
    lines.append(f"## Recovery Estimate")
    lines.append(f"")
    lines.append(f"Based on **12 months** of historical billing data:")
    lines.append(f"")
    lines.append(f"| Item | Amount |")
    lines.append(f"|------|-------:|")
    lines.append(f"| **Estimated Total Recoverable** | {format_currency(total_recoverable)} |")
    lines.append(f"| **Fee Estimate (50% of Recovery)** | {format_currency(fee_estimate)} |")
    lines.append(f"")

    # ── Next Steps ────────────────────────────────────────────────
    lines.append(f"## Recommended Next Steps")
    lines.append(f"")
    lines.append(f"1. **Review Dispute Schedule** — Examine the detailed Excel dispute")
    lines.append(f"   schedule line by line to verify all flagged items.")
    lines.append(f"")
    lines.append(f"2. **Submit Formal Dispute** — Send the generated dispute letter")
    lines.append(f"   to the account manager with the schedule attached.")
    lines.append(f"")
    lines.append(f"3. **Request Credit Note** — Request a credit note for all verified")
    lines.append(f"   overcharges covering the full audit period.")
    lines.append(f"")
    lines.append(f"4. **Engage Telco for Correction** — Require the provider to correct")
    lines.append(f"   the root causes (rate plan assignments, discount applications,")
    lines.append(f"   roaming entitlements) to prevent recurrence.")
    lines.append(f"")
    lines.append(f"5. **Schedule Follow-Up Audit** — Conduct a follow-up audit in 3-6")
    lines.append(f"   months to ensure corrections have been applied.")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"*Report generated by 1st 4 Mobile Billing Audit Pipeline*")
    lines.append(f"*{today_str}*")

    summary_text = "\n".join(lines)

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            output_file.write_text(summary_text, encoding="utf-8")
        except Exception as exc:
            logger.error(f"Failed to write executive summary to {output_path}: {exc}")
            raise IOError(f"Could not write executive summary: {exc}") from exc
        logger.info(f"Executive summary saved: {output_file.resolve()}")

    logger.info(
        f"Executive summary generated for {client_name}: "
        f"{total_flags} flags, "
        f"recoverable={format_currency(total_recoverable)}"
    )

    return summary_text
