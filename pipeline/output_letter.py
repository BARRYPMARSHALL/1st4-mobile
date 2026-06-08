"""
1st 4 Mobile — Dispute Letter Generation

Generates a formal dispute letter using a Jinja2 template embedded as
a string in this module. The letter includes a summary of findings,
total overcharge amount, account numbers, and signature blocks.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from jinja2 import Template

from pipeline.config import OUTPUT_DATE_FORMAT
from pipeline.utils.money_utils import format_currency

logger = logging.getLogger("1st4pipeline.output_letter")

# ── Jinja2 Template (embedded string) ─────────────────────────────

DISPUTE_LETTER_TEMPLATE = r"""\
{{ client_name }}
{{ client_address if client_address else '' }}
{{ client_city_state if client_city_state else '' }}

{{ date }}

**PRIVATE & CONFIDENTIAL**

{{ telco }}
Attention: Account Manager
{% if telco_address %}
{{ telco_address }}
{% endif %}

**Re: Billing Dispute — {{ client_name }}
Account{% if account_numbers|length > 1 %}s{% endif %}:
{% for acct in account_numbers %}  {{ acct }}
{% endfor %}**

Dear Sir / Madam,

**1. Introduction**

We are writing on behalf of {{ client_name }} to formally dispute
certain charges identified on the above account(s) during a
comprehensive billing audit conducted by 1st 4 Mobile.

Our audit has identified **{{ total_flags }} billing irregularities**
across the following categories, resulting in an estimated total
overcharge of **{{ total_overcharge_str }}**.

**2. Summary of Findings**

| Category | Flagged Items | Monthly Overcharge |
|----------|--------------:|-------------------:|
{% for row in summary_rows -%}
| {{ row.category }} | {{ row.count }} | {{ row.amount_str }} |
{% endfor %}
| **TOTAL** | **{{ total_flags }}** | **{{ total_overcharge_str }}** |

**Estimated annualised overcharge: {{ annualised_overcharge_str }}**
**(based on {{ historical_months }}-month billing history)**

**3. Request for Resolution**

We respectfully request that Telstra/Optus:

1. **Review** all flagged items detailed in the attached Dispute Schedule
   within **14 business days** of receipt of this letter.
2. **Issue a credit note** for the full amount of the verified
   overcharges, covering the audit period.
3. **Correct the underlying billing configuration** to prevent
   recurrence of these errors.
4. **Provide written confirmation** of the corrective actions taken.

**4. Supporting Documentation**

Attached to this letter is a detailed Dispute Schedule (Excel workbook)
containing line-item breakdowns for each flagged category, including
service IDs, detection methods, confidence ratings, and calculated
overcharge amounts.

**5. Our Commitment**

1st 4 Mobile is committed to ensuring accuracy and fairness in
telecommunications billing. We have verified all findings using
robust detection methodologies and cross-referenced them against
the contracted rate plans, discounts, and roaming entitlements
outlined in {{ client_name }}'s current service agreement.

We look forward to your prompt attention to this matter.

Yours faithfully,

__________________________               __________________________
**{{ client_name }} Representative**     **1st 4 Mobile**
                                          Billing Audit Division
                                          disputes@1st4mobile.com

**Encl:** Dispute Schedule ({{ excel_filename }})
"""


def _build_summary_rows(all_flags: dict) -> list[dict]:
    """Build a list of {category, count, amount_str} dicts for the letter table."""
    summary = all_flags.get("summary", {})

    # The run_all_detections summary dict has 'breakdown' (counts) and
    # 'monthly_breakdown' (amounts). We need per-category rows.
    breakdown = summary.get("breakdown", {})
    monthly_breakdown = summary.get("monthly_breakdown", {})

    category_labels = {
        "ghost_lines": "Ghost Lines",
        "rate_mismatches": "Rate Mismatches",
        "roaming": "Roaming Anomalies",
        "legacy_rollbacks": "Legacy Rollbacks",
        "duplicates": "Duplicates",
    }

    rows = []
    for key, label in category_labels.items():
        count = breakdown.get(key, 0)
        amount = monthly_breakdown.get(key, 0.0)
        if count > 0 or amount > 0:
            rows.append({
                "category": label,
                "count": count,
                "amount_str": format_currency(amount),
            })

    return rows


def generate_dispute_letter(
    all_flags: dict,
    client_name: str,
    telco: str,
    account_numbers: list,
    client_contact: str = None,
    output_path: str = None,
) -> str:
    """Generate a formal dispute letter using a Jinja2 template.

    Args:
        all_flags: Result dict from run_all_detections() containing
            DataFrames for each engine and a summary dict.
        client_name: Name of the client (e.g. "Acme Mining Pty Ltd").
        telco: Telecom provider name (e.g. "Telstra", "Optus").
        account_numbers: List of account number strings.
        client_contact: Optional contact person name/title.
        output_path: Optional path to write the letter file. If not
            provided, the letter text is returned as a string.

    Returns:
        The letter text as a string. If output_path was provided,
        also writes to that file and returns the text.

    Raises:
        IOError: If the file cannot be written.
    """
    summary = all_flags.get("summary", {})
    total_flags = int(summary.get("total_flags", 0))
    total_monthly = float(summary.get("total_monthly_overcharge", 0.0))
    total_annualised = float(summary.get("total_annualised", 0.0))

    historical_months = 12

    summary_rows = _build_summary_rows(all_flags)
    total_overcharge_str = format_currency(total_monthly)
    annualised_overcharge_str = format_currency(total_annualised)

    today_str = datetime.now().strftime(OUTPUT_DATE_FORMAT)

    # Determine filename for the attached Excel
    excel_filename = "Dispute_Schedule.xlsx"
    if output_path:
        # If we have an output path for the letter, derive a matching
        # Excel filename
        letter_path = Path(output_path)
        excel_filename = letter_path.stem.replace("_Letter", "_Schedule") + ".xlsx"

    template = Template(DISPUTE_LETTER_TEMPLATE, trim_blocks=True, lstrip_blocks=True)

    # Client address info (we may not have it — use empty strings)
    client_address: str = ""
    client_city_state: str = ""

    telco_address: str = ""

    letter_text = template.render(
        client_name=client_name,
        client_address=client_address,
        client_city_state=client_city_state,
        date=today_str,
        telco=telco,
        telco_address=telco_address,
        account_numbers=account_numbers,
        total_flags=total_flags,
        total_overcharge_str=total_overcharge_str,
        annualised_overcharge_str=annualised_overcharge_str,
        summary_rows=summary_rows,
        historical_months=historical_months,
        excel_filename=excel_filename,
    )

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            output_file.write_text(letter_text, encoding="utf-8")
        except Exception as exc:
            logger.error(f"Failed to write dispute letter to {output_path}: {exc}")
            raise IOError(f"Could not write dispute letter: {exc}") from exc
        logger.info(f"Dispute letter saved: {output_file.resolve()}")

    # Count total overcharge amount for logging
    total_overcharge_amt = total_monthly  # monthly

    logger.info(
        f"Dispute letter generated for {client_name}: "
        f"{total_flags} flags, "
        f"monthly overcharge={total_overcharge_str}"
    )

    return letter_text
