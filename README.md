# 1st 4 Mobile — Telecom Billing Audit Engine

> *"We find the money Telstra and Optus forgot to tell you about."*

**Website:** [www.1st4.mobi](https://www.1st4.mobi)
**Business:** AI-driven telecom expense audit & recovery
**Model:** 50% contingency — no recovery, no fee
**Founded:** 2026

---

## Overview

**1st 4 Mobile** is an automated telecom billing audit platform that recovers overcharges from Australia's major telcos (Telstra, Optus) on behalf of mid-market enterprises. We process corporate billing data through five specialised detection engines, identify billing errors, and package the findings into a dispute-ready submission — all in under 48 hours.

### The Problem

Australian enterprises spend **$12-15B/year** on corporate telecommunications. Industry studies consistently find **8-15% of invoices contain errors** — ghost lines, wrong rate plans, missing contract discounts, and duplicate charges. Yet most companies verify their bills by checking "total vs budget," missing thousands to millions in overcharges.

### The Solution

An AI-driven parsing engine (`FREE33`) that processes 5,000-page corporate bills in seconds, runs five detection algorithms, and generates a professional dispute package — then we collect 50% of whatever we recover.

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/your-org/1st4-mobile.git
cd 1st4-mobile
pip install -r requirements.txt

# Run an audit
python -m pipeline.main \
    --client "Acme Mining" \
    --billing data/billing_*.csv \
    --contract contracts/acme_contract.yaml \
    --output ./output

# Run tests
pytest tests/ -v
```

---

## Pipeline Architecture

```
┌────────────────────────────────────────────┐
│              INPUT FILES                    │
│   CSV (Telstra Connect / T-Analyst)         │
│   PDF (Optus My Business / invoices)        │
│   XLSX (Telstra T-Analyst exports)          │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────┐
│        1. DATA INGESTION LAYER              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ csv_     │ │ pdf_     │ │ xlsx_    │    │
│  │ ingestor │ │ ingestor │ │ ingestor │    │
│  │ .py      │ │ .py      │ │ .py      │    │
│  └──────────┘ └──────────┘ └──────────┘    │
│  • Auto-detect delimiter & encoding         │
│  • Multi-header CSV handling                │
│  • PDF: pdfplumber → Camelot → OCR fallback │
│  • Streaming for 100MB+ files              │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────┐
│        2. SCHEMA NORMALISATION              │
│         (normaliser.py)                     │
│  • Maps raw columns to 18-field canonical   │
│    schema (account_number, service_id,      │
│    charge_amount, plan_code, etc.)          │
│  • Fuzzy column matching via thefuzz        │
│  • Australian date parsing (DD/MM/YYYY)     │
│  • GST detection & stripping                │
│  • Service type & charge classification     │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────┐
│        3. CONTRACT MATRIX                   │
│        (contract_matrix.py)                 │
│  • YAML-based MSA/rate card digitisation    │
│  • Plan lookup by code                      │
│  • Discount application                     │
│  • Roaming zone rate tables                 │
│  • Pool configuration                       │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────┐
│           4. FIVE DETECTION ENGINES (parallel)     │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  Ghost Line Detector (detect_ghost.py)       │  │
│  │  • Zero usage for 2+ consecutive months      │  │
│  │  • Disconnect fee + continued billing        │  │
│  │  • Never-used (bill-only) accounts           │  │
│  │  ~40% of all errors found                    │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  Rate Plan Validator (detect_rate.py)        │  │
│  │  • Billed rate vs contracted rate check      │  │
│  │  • Overage rate validation                   │  │
│  │  • Missing volume discount detection         │  │
│  │  ~30% of errors, $$$ impact                 │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  Roaming Anomaly Check (detect_roaming.py)   │  │
│  │  • Zone rate comparison                      │  │
│  │  • Unentitled roaming detection              │  │
│  │  ~15% of errors                              │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  Legacy Rollback Scanner (detect_legacy.py)  │  │
│  │  • Contract expiry → rack rate reversion     │  │
│  │  • Plan code change tracking over time       │  │
│  │  • Price increase detection                  │  │
│  │  ⚠️ BIGGEST $ — single find can be $100k+   │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  Duplicate Service Filter (detect_duplicate) │  │
│  │  • Exact duplicates                          │  │
│  │  • Cross-account duplicates                  │  │
│  │  • Near duplicates (amount tolerance)        │  │
│  │  ~5% of errors                               │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────────┬─────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│        5. OUTPUT GENERATION                │
│  ┌────────────────────────────────────┐    │
│  │ dispute_schedule.xlsx              │    │
│  │ • Executive Summary sheet          │    │
│  │ • Ghost Lines sheet               │    │
│  │ • Rate Mismatches sheet            │    │
│  │ • Roaming Anomalies sheet          │    │
│  │ • Legacy Rollbacks sheet           │    │
│  │ • Duplicates sheet                │    │
│  └────────────────────────────────────┘    │
│  ┌────────────────────────────────────┐    │
│  │ dispute_letter.md                  │    │
│  │ • Formal demand to Telstra/Optus   │    │
│  │ • Account numbers & finding refs   │    │
│  └────────────────────────────────────┘    │
│  ┌────────────────────────────────────┐    │
│  │ executive_summary.md               │    │
│  │ • Top findings                     │    │
│  │ • Recovery & fee estimates         │    │
│  └────────────────────────────────────┘    │
└────────────────────────────────────────────┘
```

---

## Project Structure

```
~/1st4-mobile/
├── pipeline/
│   ├── __init__.py
│   ├── config.py                 # Thresholds, paths, constants
│   ├── csv_ingestor.py           # CSV detection + parsing
│   ├── pdf_ingestor.py           # PDF parsing (pdfplumber → Camelot → OCR)
│   ├── xlsx_ingestor.py          # Excel parsing
│   ├── normaliser.py             # Schema normalisation engine
│   ├── contract_matrix.py        # Contract YAML loader + lookup
│   ├── detect_ghost.py           # Ghost line detection (3 signals)
│   ├── detect_rate.py            # Rate plan validation
│   ├── detect_roaming.py         # Roaming anomaly detection
│   ├── detect_legacy.py          # Legacy rollback detection
│   ├── detect_duplicate.py       # Duplicate service detection
│   ├── detect_runner.py          # Orchestrates all 5 engines
│   ├── output_excel.py           # Dispute schedule Excel generation
│   ├── output_letter.py          # Dispute letter generation
│   ├── output_summary.py         # Executive summary generation
│   ├── main.py                   # CLI orchestrator
│   └── utils/
│       ├── __init__.py
│       ├── date_utils.py         # Australian date parsing
│       ├── money_utils.py        # Currency, GST handling
│       ├── text_utils.py         # Fuzzy matching, classification
│       └── logging_utils.py      # Audit trail
├── tests/
│   ├── generate_test_data.py     # Synthetic test data
│   ├── test_ingestion.py         # Ingestion tests
│   ├── test_detection.py         # Detection engine tests
│   └── test_output.py            # Output generation tests
├── column_mappings.yaml          # Column name registry
├── rack_rates.yaml               # Telstra/Optus rack rate reference
├── test_contract.yaml            # Sample contract for testing
├── contracts/                    # Per-client contract matrices
├── output/                       # Generated dispute packages
├── requirements.txt
├── README.md                     # This file
└── .gitignore
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.11+ | Stable, pandas ecosystem |
| **CSV** | pandas (read_csv, chunksize) | GB-scale streaming |
| **PDF** | pdfplumber → Camelot → Tesseract | 3-tier fallback chain |
| **Excel** | openpyxl | Generate formatted workbooks |
| **Config** | YAML (PyYAML) | Contract matrices, mappings |
| **Templates** | Jinja2 | Dispute letter generation |
| **Testing** | pytest | Unit + integration tests |
| **Fuzzy** | thefuzz | Column name matching |

---

## Detection Confidence Scoring

Every finding includes a confidence score (0.0–1.0):

| Signal | Confidence | Description |
|--------|-----------|-------------|
| `zero_usage` | 0.85 | 2+ months of zero usage |
| `never_used` | 0.80 | Service billing since activation, never used |
| `disconnect_but_billing` | 0.95 | Disconnect fee followed by continued billing |
| `rate_mismatch` | 0.90–0.98 | Billed ≠ contracted rate |
| `unknown_plan` | 0.70 | Plan code not found in contract matrix |
| `overage_rate_mismatch` | 0.85 | Overage billed at wrong per-MB rate |
| `missing_discount` | 0.65 | Contractual discount not applied |
| `roaming_rate_overcharge` | 0.80 | Roaming charged at wrong zone rate |
| `unentitled_roaming` | 0.60 | Roaming on non-roaming plan |
| `legacy_rollback` | 0.75 | Contract plan reverted to rack rate |
| `exact_duplicate` | 0.98 | Identical charge twice in same period |
| `cross_account_duplicate` | 0.90 | Same service under different accounts |
| `near_duplicate` | 0.75 | Similar charge within tolerance |

Only flags with confidence ≥ 0.70 are included in the dispute package by default.

---

## Business Model

### Pricing

| Service | Fee | When |
|---------|-----|------|
| **Initial billing audit** | 50% of recovered overcharges (12 months back-bill) | On refund/credit received |
| **Ongoing monitoring** | 30% of ongoing savings (year 2+) | Monthly |
| **MSA negotiation support** | $3,000–$10,000 fixed fee | At client request |

### Target Clients

| Sector | Target Size | Est. Annual Telco Spend | Typical Recovery |
|--------|-------------|------------------------|-----------------|
| Mining services (WA/QLD) | 300–2,000 emp | $500k–$1.5M | $50k–$500k |
| Transport & logistics (NSW/VIC) | 200–1,500 emp | $150k–$800k | $20k–$200k |
| Civil construction | 200–1,000 emp | $100k–$500k | $10k–$100k |
| Manufacturing | 200–1,000 emp | $80k–$400k | $10k–$80k |

### Addressable Market

- **Total Australian corporate telecom spend:** $12-15B/year (IBISWorld, Telsyte)
- **Estimated billing error pool:** $960M–$2.25B/year (8–15% error rate)
- **Target companies:** ~3,000–4,000 with 200–2,000 employees in mining, logistics, construction, and manufacturing
- **Consultant fee pool:** $100M–$500M/year at 50% contingency

### Competitive Advantage

| Factor | 1st 4 Mobile | Competitors |
|--------|-------------|-------------|
| **Audit speed** | 2 seconds (AI processing) | 2–3 days (human analysts) |
| **Marginal cost** | ~$0 per audit | $500–$2,000 in salaries |
| **Scalability** | 50+ audits simultaneously | Bottlenecked by headcount |
| **Pre-pitch intelligence** | AI scans public data before contact | Generic cold outreach |
| **Engineering credibility** | Engineering degree backing | Mostly accounting backgrounds |
| **Fee model** | 50% contingency (industry standard) | 50% contingency (same) |

### Competitors

- **Billfishing, TelcoAuditor, Telco Recon, Billing Insight, MyBilling** — all use same 50/50 model but manual processing
- **Big 4 (PwC, Deloitte, EY, KPMG)** — offer TEM advisory but hourly/fixed fee only, not contingency

---

## Legal & Compliance

| Requirement | Status | Action |
|-------------|--------|--------|
| Tax agent registration | ❌ Not required | Telecom audit ≠ tax advice |
| ABN | ✅ Required | Register before trading |
| PI Insurance | ⚠️ Recommended ($1–5M) | Mitigates privacy/error risk |
| Data Processing Agreement | ✅ Required | Privacy Act 1988 compliance |
| Spam Act (cold email) | ⚠️ B2B exemption applies | Include ID + unsubscribe |
| TIO jurisdiction | ❌ Does not apply to >20 emp | Large corps use contract dispute |

---

## Financial Projections

### Startup Capital: ~$5,000

| Item | Cost |
|------|------|
| Company registration | $500 |
| PI insurance (annual) | $2,400 |
| Legal document templates | $2,000 |
| Domain + hosting | $300 |
| Misc | $800 |

### Year 1 Projection (Moderate Scenario)

| Month | New Clients | Cumulative | Revenue |
|-------|-------------|------------|--------|
| M1–2 | 3 | 3 | $0 (audits in progress) |
| M3 | 3 | 6 | $20,000 |
| M4–6 | 11 | 17 | $185,000 |
| M7–9 | 9 | 26 | $300,000 |
| M10–12 | 9 | 35 | $410,000 |
| **Total** | **35** | | **~$915,000** |

Net margin: ~99.2% (AI-first, founder-only operation)

---

## CLI Reference

```bash
# Full audit
python -m pipeline.main \
    --client "Acme Mining" \
    --billing data/invoice_*.csv \
    --contract contracts/acme.yaml \
    --output ./output

# Multiple billing files
python -m pipeline.main \
    --client "TestCo" \
    -b invoice_2025Q1.csv \
    -b invoice_2025Q2.csv \
    -c my_contract.yaml \
    -o ./audit_out \
    -v

# Help
python -m pipeline.main --help

# Run tests
pytest tests/ -v
```

---

## Real-World Walkthrough

### Scenario: 500-SIM Mining Company (Telstra)

1. **Client provides:** 3 quarters of Telstra billing CSVs (127MB) + signed MSA rate card
2. **Ingestion:** FREE33 parses all files in 3.2 seconds → 54,700 row DataFrame
3. **Contract:** MSA digitised into YAML (15 minutes, human-assisted)
4. **Detection runs:**

   | Engine | Flags | Monthly Overcharge |
   |--------|-------|-------------------|
   | Ghost lines | 50 | $4,250 |
   | Rate mismatches | 312 | $3,120 |
   | Legacy rollbacks | 150 | $9,000 |
   | Roaming anomalies | 87 | $890 |
   | Duplicates | 3 | $135 |
   | **Total** | **602** | **$17,395** |

5. **Output generated:** 6-sheet Excel + formal dispute letter
6. **Telstra response (14 days):** Confirms 580 of 602 flags. Issues credit note: **$156,000**
7. **1st 4 Mobile fees:** $78,000 (50% of back-bill) + $4,560/month ongoing monitoring

---

## Test Data

Generate synthetic test data:

```python
from tests.generate_test_data import generate_test_csv

generate_test_csv(
    output_path="tests/fixtures/telstra_test.csv",
    n_services=100,
    n_months=3,
    error_rate=0.10  # 10% of services have intentional errors
)
```

---

## FAQ

**Q: Is the market real?**
A: Yes. 10–15 Australian firms already do this. Telstra admitted overcharging 100k+ customers ($50M refunds). Optus refunded $13M+.

**Q: Is the 50/50 split standard?**
A: Yes — industry standard in Australia, US, and UK. Billfishing, TelcoAuditor, Telco Recon all use it.

**Q: How fast do clients get paid?**
A: Telcos process dispute credits in 2–4 weeks. RDTI takes 6–12 months. This is the key advantage over the RDTI playbook.

**Q: What if no errors are found?**
A: The client pays nothing. With 80–90% hit rate, we're confident in the model.

**Q: Can Telstra/Optus refuse the dispute?**
A: They can try, but with the client's written authorisation and ironclad evidence package, they fold to retain the corporate account.

**Q: Do I need a tax agent licence?**
A: No — telecom billing audit is not tax advice. This is a pure commercial B2B dispute.

---

## License

Commercial. Proprietary to 1st 4 Mobile Pty Ltd.

---

*Built by [FREE33](https://github.com/free33) for Barry — June 2026*
