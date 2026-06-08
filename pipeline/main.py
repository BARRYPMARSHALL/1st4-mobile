"""
1st 4 Mobile — Main Audit Pipeline Orchestrator

Entry point for running the full billing audit pipeline:
  1. Input validation
  2. File format detection and ingestion
  3. Contract matrix loading
  4. Rack rates loading
  5. Schema normalisation
  6. All 5 detection engines
  7. Excel dispute schedule generation
  8. Dispute letter generation
  9. Executive summary generation

CLI usage:
    python -m pipeline.main \\
        --client "Acme Mining" \\
        --billing data/invoice_*.csv \\
        --contract contract.yaml \\
        --output ./output
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# ── Ingestion ─────────────────────────────────────────────────────
from pipeline.config import (
    OUTPUT_DIR,
    OUTPUT_DATE_FORMAT,
)
from pipeline.csv_ingestor import ingest_csv
from pipeline.xlsx_ingestor import ingest_xlsx
from pipeline.pdf_ingestor import detect_and_ingest_pdf
from pipeline.normaliser import normalise
from pipeline.contract_matrix import ContractMatrix, load_contract
from pipeline.detect_runner import run_all_detections

# ── Output ────────────────────────────────────────────────────────
from pipeline.output_excel import generate_dispute_schedule
from pipeline.output_letter import generate_dispute_letter
from pipeline.output_summary import generate_executive_summary

# ── Utilities ─────────────────────────────────────────────────────
from pipeline.utils.logging_utils import setup_logging, AuditLogger
from pipeline.utils.date_utils import parse_date

logger = logging.getLogger("1st4pipeline.main")


# ── Format Detection ──────────────────────────────────────────────


def _detect_format(file_path: str) -> str:
    """Detect billing file format based on extension.

    Args:
        file_path: Path to the billing file.

    Returns:
        One of 'csv', 'xlsx', 'pdf', or raises ValueError.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".csv":
        return "csv"
    elif ext in (".xlsx", ".xls"):
        return "xlsx"
    elif ext == ".pdf":
        return "pdf"
    else:
        raise ValueError(
            f"Unsupported file format '{ext}' for {file_path}. "
            f"Supported: .csv, .xlsx, .xls, .pdf"
        )


def _ingest_file(file_path: str) -> tuple:
    """Ingest a single billing file, auto-detecting its format.

    Args:
        file_path: Path to the billing file.

    Returns:
        Tuple of (DataFrame, audit_info_dict).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the format is unsupported or ingestion fails.
    """
    file_path = str(Path(file_path).resolve())
    fmt = _detect_format(file_path)
    logger.info(f"Detected format '{fmt}' for {file_path}")

    if fmt == "csv":
        df, audit_info = ingest_csv(file_path)
    elif fmt == "xlsx":
        df, audit_info = ingest_xlsx(file_path)
    elif fmt == "pdf":
        df, audit_info = detect_and_ingest_pdf(file_path)
    else:
        raise ValueError(f"Unsupported format: {fmt}")

    # Attach provider to audit_info for normalisation
    provider = audit_info.get("provider", "unknown")

    # Normalise
    df_norm, unmapped = normalise(df, source_file=file_path, provider=provider)

    logger.info(
        f"Ingested {file_path}: {len(df_norm)} normalised rows "
        f"({len(unmapped)} unmapped columns)"
    )

    return df_norm, audit_info


def _load_rack_rates(rack_rates_path: str) -> Optional[dict]:
    """Load rack rates from a YAML file.

    Args:
        rack_rates_path: Path to the rack_rates.yaml file.

    Returns:
        Dict of {plan_code: rate} or None if not provided/missing.
    """
    if not rack_rates_path:
        return None

    path = Path(rack_rates_path)
    if not path.exists():
        logger.warning(f"Rack rates file not found: {rack_rates_path}")
        return None

    try:
        from yaml import safe_load

        with open(path, "r", encoding="utf-8") as fh:
            data = safe_load(fh)

        if not isinstance(data, dict):
            logger.warning(f"Rack rates file has unexpected format, expected dict")
            return None

        # Expect a mapping of {plan_code: rate}
        rack_rates = {}
        for key, val in data.items():
            if isinstance(val, (int, float)):
                rack_rates[str(key)] = float(val)

        logger.info(f"Loaded {len(rack_rates)} rack rate entries from {path.name}")
        return rack_rates
    except Exception as exc:
        logger.warning(f"Failed to load rack rates from {rack_rates_path}: {exc}")
        return None


def _validate_inputs(
    billing_files: list[str],
    contract_matrix_path: str,
    rack_rates_path: Optional[str] = None,
) -> dict:
    """Validate that all input files exist and are accessible.

    Args:
        billing_files: List of billing file paths.
        contract_matrix_path: Path to contract YAML.
        rack_rates_path: Optional path to rack rates YAML.

    Returns:
        Dict with per-file status: {'file': path, 'exists': bool, 'error': ...}

    Raises:
        FileNotFoundError: If any required file is missing.
    """
    logger.info("Validating input files...")
    results = []

    # Validate billing files
    seen = set()
    for bf in billing_files:
        resolved = str(Path(bf).resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        path = Path(bf)
        if not path.exists():
            results.append({"file": bf, "exists": False, "error": "File not found"})
            logger.error(f"Billing file not found: {bf}")
            raise FileNotFoundError(f"Billing file not found: {bf}")
        results.append({"file": bf, "exists": True, "error": None})

    # Validate contract matrix
    cm_path = Path(contract_matrix_path)
    if not cm_path.exists():
        logger.error(f"Contract matrix not found: {contract_matrix_path}")
        raise FileNotFoundError(f"Contract matrix not found: {contract_matrix_path}")
    results.append({"file": str(cm_path.resolve()), "exists": True, "error": None})

    # Validate rack rates (optional)
    if rack_rates_path:
        rr_path = Path(rack_rates_path)
        if not rr_path.exists():
            logger.warning(f"Rack rates file not found: {rack_rates_path}")

    return results


def _build_result(
    all_flags: dict,
    excel_path: str = None,
    letter_path: str = None,
    summary_path: str = None,
    audit: AuditLogger = None,
) -> dict:
    """Build the final result dict returned by run_audit()."""
    summary = all_flags.get("summary", {})
    total_flags = int(summary.get("total_flags", 0))
    total_monthly = float(summary.get("total_monthly_overcharge", 0.0))
    total_annualised = float(summary.get("total_annualised", 0.0))

    result = {
        "summary": {
            "total_flags": total_flags,
            "total_monthly_overcharge": total_monthly,
            "total_annualised": total_annualised,
            "breakdown": summary.get("breakdown", {}),
            "monthly_breakdown": summary.get("monthly_breakdown", {}),
        },
        "output_files": {
            "excel_schedule": excel_path,
            "dispute_letter": letter_path,
            "executive_summary": summary_path,
        },
        "audit_log": audit.summary() if audit else "No audit trail",
    }

    return result


# ── Main Pipeline ─────────────────────────────────────────────────


def run_audit(
    client_name: str,
    billing_files: list[str],
    contract_matrix_path: str,
    output_dir: str = None,
    rack_rates_path: str = None,
    verbose: bool = False,
) -> dict:
    """Run the full billing audit pipeline.

    Flow:
        1. Set up logging and audit trail
        2. Validate all input files exist
        3. For each billing file: detect format → ingest → concatenate
        4. Load contract matrix from YAML
        5. Load rack rates from YAML
        6. Normalise to canonical schema
        7. Run all 5 detection engines
        8. Generate Excel dispute schedule
        9. Generate dispute letter
       10. Generate executive summary
       11. Return result dict

    Args:
        client_name: Name of the client being audited.
        billing_files: List of paths to billing invoice files.
        contract_matrix_path: Path to the contract matrix YAML file.
        output_dir: Directory for output files. Defaults to config.OUTPUT_DIR.
        rack_rates_path: Optional path to rack_rates.yaml.
        verbose: If True, enable DEBUG-level logging.

    Returns:
        Dict with keys:
            summary       — dict with total_flags, totals, breakdowns
            output_files  — dict of {excel_schedule, dispute_letter, executive_summary}
            audit_log     — audit trail string

    Raises:
        FileNotFoundError: If required input files are missing.
        ValueError: If inputs are invalid or no billing files provided.
    """
    # ── Step 0: Setup ─────────────────────────────────────────────
    if output_dir is None:
        output_dir = str(OUTPUT_DIR)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    log_dir = str(output_path / "logs")
    setup_logging(log_dir=log_dir, verbose=verbose)

    audit = AuditLogger()

    logger.info("=" * 60)
    logger.info(f"1st 4 Mobile Billing Audit Pipeline")
    logger.info(f"Client: {client_name}")
    logger.info(f"Output: {output_path.resolve()}")
    logger.info(f"Billing files: {len(billing_files)}")
    logger.info("=" * 60)

    audit.log(
        "pipeline", "start",
        f"Starting audit for {client_name} with {len(billing_files)} billing file(s)",
    )

    # ── Step 1: Validate Inputs ──────────────────────────────────
    logger.info("─" * 50)
    logger.info("Step 1/10: Validating input files")
    try:
        _validate_inputs(billing_files, contract_matrix_path, rack_rates_path)
        logger.info("  → All input files validated successfully")
    except FileNotFoundError as exc:
        logger.error(f"Input validation failed: {exc}")
        audit.log("pipeline", "error", f"Input validation failed: {exc}")
        raise
    audit.log("pipeline", "validate_inputs", "All input files validated", count=len(billing_files))

    # ── Step 2: Ingest Billing Files ──────────────────────────────
    logger.info("─" * 50)
    logger.info("Step 2/10: Ingesting billing files")

    dfs: list[pd.DataFrame] = []
    total_rows = 0

    for i, bf in enumerate(billing_files, 1):
        logger.info(f"  [{i}/{len(billing_files)}] Ingesting {Path(bf).name}")
        try:
            df_norm, ingest_audit = _ingest_file(bf)
            dfs.append(df_norm)
            total_rows += len(df_norm)
            audit.log(
                "ingest", Path(bf).name,
                f"Ingested {len(df_norm)} rows, provider={ingest_audit.get('provider', 'unknown')}",
                count=len(df_norm),
            )
        except Exception as exc:
            logger.error(f"  ✗ Failed to ingest {bf}: {exc}")
            audit.log("ingest", "error", f"Failed to ingest {bf}: {exc}")
            # Continue with other files — don't abort the whole pipeline
            continue

    if not dfs:
        error_msg = "No billing files could be ingested successfully"
        logger.error(error_msg)
        audit.log("pipeline", "error", error_msg)
        raise ValueError(error_msg)

    df_combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"  → Combined: {len(df_combined)} total rows across {len(billing_files)} file(s)")
    audit.log("pipeline", "ingest_complete", f"Combined {len(df_combined)} rows", count=len(df_combined))

    # ── Step 3: Load Contract Matrix ──────────────────────────────
    logger.info("─" * 50)
    logger.info("Step 3/10: Loading contract matrix")
    try:
        contract = ContractMatrix(contract_matrix_path)
        logger.info(f"  → Contract loaded: '{contract.client_name}', {len(contract.plan_codes)} plans")
        audit.log(
            "contract", "loaded",
            f"Contract '{contract.client_name}' with {len(contract.plan_codes)} plans",
            count=len(contract.plan_codes),
        )
    except Exception as exc:
        logger.error(f"  ✗ Failed to load contract matrix: {exc}")
        audit.log("contract", "error", f"Failed to load contract: {exc}")
        raise

    # ── Step 4: Load Rack Rates (optional) ────────────────────────
    logger.info("─" * 50)
    logger.info("Step 4/10: Loading rack rates")
    if rack_rates_path:
        rack_rates = _load_rack_rates(rack_rates_path)
        if rack_rates:
            logger.info(f"  → Loaded {len(rack_rates)} rack rate entries")
            audit.log("rack_rates", "loaded", f"Loaded {len(rack_rates)} entries", count=len(rack_rates))
        else:
            logger.info("  → No rack rates loaded (file missing or empty)")
            audit.log("rack_rates", "skipped", "No rack rates loaded")
    else:
        rack_rates = None
        logger.info("  → No rack rates file provided — skipping")
        audit.log("rack_rates", "skipped", "Not provided")

    # ── Step 5: Normalise (already done per-file, but log) ────────
    logger.info("─" * 50)
    logger.info("Step 5/10: Schema normalisation (completed per-file during ingestion)")
    audit.log("normaliser", "complete", f"All {len(dfs)} files normalised", count=len(df_combined))

    # ── Step 6: Run Detection Engines ─────────────────────────────
    logger.info("─" * 50)
    logger.info("Step 6/10: Running detection engines")
    try:
        all_flags = run_all_detections(df_combined, contract, rack_rates=rack_rates, audit=audit)
    except Exception as exc:
        logger.error(f"  ✗ Detection engines failed: {exc}")
        audit.log("detection", "error", f"Detection engines failed: {exc}")
        raise

    summary = all_flags.get("summary", {})
    total_flags = int(summary.get("total_flags", 0))
    total_monthly = float(summary.get("total_monthly_overcharge", 0.0))

    logger.info(f"  → Detection complete: {total_flags} flags, ${total_monthly:.2f}/month")
    audit.log(
        "detection", "complete",
        f"All engines complete: {total_flags} flags",
        count=total_flags,
        amount=round(total_monthly, 2),
    )

    # ── Step 7: Generate Dispute Schedule (Excel) ─────────────────
    logger.info("─" * 50)
    logger.info("Step 7/10: Generating Excel dispute schedule")
    excel_path = str(output_path / f"Dispute_Schedule_{client_name.replace(' ', '_')}.xlsx")
    try:
        excel_path = generate_dispute_schedule(
            all_flags=all_flags,
            df_raw=df_combined,
            client_name=client_name,
            output_path=excel_path,
            contract=contract,
            audit=audit,
        )
        logger.info(f"  → Excel schedule: {excel_path}")
    except Exception as exc:
        logger.error(f"  ✗ Excel generation failed: {exc}")
        audit.log("output", "error", f"Excel schedule generation failed: {exc}")
        excel_path = None

    # ── Step 8: Generate Dispute Letter ───────────────────────────
    logger.info("─" * 50)
    logger.info("Step 8/10: Generating dispute letter")

    # Get account numbers from contract
    account_numbers_raw = contract.account_numbers
    account_numbers: list[str] = []
    for provider_key, accts in account_numbers_raw.items():
        if isinstance(accts, list):
            account_numbers.extend(accts)

    if not account_numbers:
        account_numbers = ["N/A"]

    # Determine telco name from account numbers or contract
    telco = "Telstra"
    if account_numbers_raw and len(str(account_numbers_raw)) > 0:
        # Use the first provider key that has accounts
        for prov in ["telstra", "optus"]:
            if account_numbers_raw.get(prov, []):
                telco = prov.capitalize()
                break

    letter_path = str(output_path / f"Dispute_Letter_{client_name.replace(' ', '_')}.txt")
    try:
        letter_text = generate_dispute_letter(
            all_flags=all_flags,
            client_name=client_name,
            telco=telco,
            account_numbers=account_numbers,
            client_contact=None,
            output_path=letter_path,
        )
        logger.info(f"  → Dispute letter: {letter_path}")
        audit.log("output", "letter", f"Dispute letter generated for {telco}")
    except Exception as exc:
        logger.error(f"  ✗ Letter generation failed: {exc}")
        audit.log("output", "error", f"Dispute letter generation failed: {exc}")
        letter_path = None

    # ── Step 9: Generate Executive Summary ────────────────────────
    logger.info("─" * 50)
    logger.info("Step 9/10: Generating executive summary")
    summary_path = str(output_path / f"Executive_Summary_{client_name.replace(' ', '_')}.md")
    try:
        summary_text = generate_executive_summary(
            all_flags=all_flags,
            client_name=client_name,
            total_recoverable=summary.get("total_annualised"),
            output_path=summary_path,
        )
        logger.info(f"  → Executive summary: {summary_path}")
        audit.log("output", "summary", "Executive summary generated")
    except Exception as exc:
        logger.error(f"  ✗ Summary generation failed: {exc}")
        audit.log("output", "error", f"Executive summary generation failed: {exc}")
        summary_path = None

    # ── Step 10: Return Results ───────────────────────────────────
    logger.info("─" * 50)
    logger.info("Step 10/10: Audit complete")

    result = _build_result(
        all_flags=all_flags,
        excel_path=excel_path,
        letter_path=letter_path,
        summary_path=summary_path,
        audit=audit,
    )

    logger.info("=" * 60)
    logger.info(f"AUDIT COMPLETE — {client_name}")
    logger.info(f"  Total flags:             {result['summary']['total_flags']}")
    logger.info(f"  Monthly overcharge:      ${result['summary']['total_monthly_overcharge']:.2f}")
    logger.info(f"  Annualised overcharge:   ${result['summary']['total_annualised']:.2f}")
    logger.info(f"  Excel schedule:          {excel_path or 'FAILED'}")
    logger.info(f"  Dispute letter:          {letter_path or 'FAILED'}")
    logger.info(f"  Executive summary:       {summary_path or 'FAILED'}")
    logger.info("=" * 60)

    audit.log(
        "pipeline", "complete",
        f"Audit complete for {client_name}: {total_flags} flags, "
        f"${total_monthly:.2f}/month",
        count=total_flags,
        amount=round(total_monthly, 2),
    )

    return result


# ── CLI Entry Point ───────────────────────────────────────────────


def main():
    """CLI entry point for the audit pipeline.

    Parses command-line arguments and runs the full audit.

    Usage:
        python -m pipeline.main \\
            --client "Acme Mining" \\
            --billing data/*.csv \\
            --contract contract.yaml \\
            --output ./output
    """
    parser = argparse.ArgumentParser(
        description="1st 4 Mobile — Telecom Billing Audit Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m pipeline.main --client "Acme Mining" --billing data/*.csv --contract contract.yaml
  python -m pipeline.main --client "TestCo" -b invoice.csv -b invoice2.csv -c my_contract.yaml -o ./audit_out -v
        """,
    )

    parser.add_argument(
        "--client", "-n",
        type=str,
        required=True,
        help="Client name (e.g. 'Acme Mining Pty Ltd')",
    )
    parser.add_argument(
        "--billing", "-b",
        type=str,
        required=True,
        nargs="+",
        help="Billing invoice file(s) — supports glob patterns (e.g. data/invoice_*.csv)",
    )
    parser.add_argument(
        "--contract", "-c",
        type=str,
        required=True,
        help="Path to contract matrix YAML file",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory for generated files (default: ./output)",
    )
    parser.add_argument(
        "--rack-rates", "-r",
        type=str,
        default=None,
        help="Path to rack_rates.yaml (optional)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable DEBUG-level logging",
    )

    args = parser.parse_args()

    # Expand glob patterns in billing files
    expanded_files: list[str] = []
    for pattern in args.billing:
        matched = list(Path().glob(pattern))
        if not matched:
            # Try resolving relative to current directory
            matched = list(Path.cwd().glob(pattern))
        if not matched:
            # Maybe it's an exact path
            p = Path(pattern)
            if p.exists():
                matched = [p]
        if not matched:
            logger.warning(f"No files matched pattern: {pattern}")
            continue
        expanded_files.extend(str(m.resolve()) for m in matched)

    if not expanded_files:
        print("ERROR: No billing files found matching the provided patterns.")
        sys.exit(1)

    # Deduplicate
    expanded_files = list(dict.fromkeys(expanded_files))

    try:
        result = run_audit(
            client_name=args.client,
            billing_files=expanded_files,
            contract_matrix_path=args.contract,
            output_dir=args.output,
            rack_rates_path=args.rack_rates,
            verbose=args.verbose,
        )

        print("\n✅ Audit complete!")
        print(f"   Total flags: {result['summary']['total_flags']}")
        print(f"   Monthly overcharge: ${result['summary']['total_monthly_overcharge']:.2f}")
        print(f"   Annualised: ${result['summary']['total_annualised']:.2f}")

        if result["output_files"]["excel_schedule"]:
            print(f"   📊 Excel: {result['output_files']['excel_schedule']}")
        if result["output_files"]["dispute_letter"]:
            print(f"   📄 Letter: {result['output_files']['dispute_letter']}")
        if result["output_files"]["executive_summary"]:
            print(f"   📝 Summary: {result['output_files']['executive_summary']}")

    except Exception as exc:
        print(f"\n❌ Audit failed: {exc}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
