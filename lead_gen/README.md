# ASIC/ABR Company Scraper — Australian Corporate Telco Lead Generation

Scrapes the **Australian Business Register (ABR)** public website to find active
Australian companies across target industries, for use in corporate mobile plan
lead generation.

## How It Works

The scraper uses the **ABR public web search** (no API key needed) to find
companies by industry-related keywords. For each company found, it fetches the
ABN detail page to extract:

-   **Company name**
-   **ABN** (Australian Business Number)
-   **ACN** (Australian Company Number, if registered with ASIC)
-   **Registered address** (main business location)
-   **State & Postcode**
-   **Industry classification** (ANZSIC code mapped from search keywords)
-   **Entity type** (filtered to actual companies, not trading/business names)
-   **ABN status** (active only)
-   **GST status**
-   **Source URL** (link to ABN Lookup page)

Results are saved as a CSV file ready for import into a CRM or lead management
system.

## Quick Start

```bash
# Default: search 5 industries, collect up to 200 companies
python asic_scraper.py

# Custom output file
python asic_scraper.py --output /path/to/leads.csv

# Fewer companies, specific industries
python asic_scraper.py --max-companies 50 --industries mining construction transport
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--industries` | mining, construction, transport, healthcare, professional_services | Industry filters (space-separated). See `--list-industries` for all options. |
| `--max-companies` | 200 | Maximum total companies to collect across all industries |
| `--output` | `leads.csv` (in same directory) | Output CSV file path |
| `--delay` | 1.5 | Base delay in seconds between requests (adds jitter automatically) |
| `--abn-guid` | _(none)_ | ABR Web Services API GUID for enriched data (ANZSIC codes, employee counts) |
| `--verbose` | false | Enable debug logging |
| `--list-industries` | — | List all available industry filters and exit |

## Example Commands

```bash
# List available industries
python asic_scraper.py --list-industries

# Focus on mining and construction companies
python asic_scraper.py --industries mining construction --max-companies 100

# Full suite with all industries (will take longer but gathers more leads)
python asic_scraper.py --industries mining construction transport healthcare \
    professional_services wholesale manufacturing retail hospitality agriculture

# With ABR API GUID for enriched ANZSIC and employee count data
python asic_scraper.py --abn-guid "ABCDEF12-1234-5678-90AB-CDEF12345678"
```

## Available Industries

The scraper includes built-in keyword mappings for these industry groups:

| Key | Description | ANZSIC Division |
|-----|-------------|-----------------|
| `mining` | Mining | B |
| `construction` | Construction | E |
| `transport` | Transport, Postal & Warehousing | I |
| `healthcare` | Health Care & Social Assistance | Q |
| `professional_services` | Professional, Scientific & Technical Services | M |
| `wholesale` | Wholesale Trade | F |
| `manufacturing` | Manufacturing | C |
| `retail` | Retail Trade | G |
| `hospitality` | Accommodation & Food Services | H |
| `agriculture` | Agriculture, Forestry & Fishing | A |

Each industry uses multiple keyword searches (e.g., "Mining", "Mine", "Resources",
"Mineral") to find relevant companies.

## Data Source: ABR (Australian Business Register)

### Public Web Search (used by default — no API key needed)

The scraper uses the public ABN Lookup search at
[https://abr.business.gov.au/Search/ResultsActive](https://abr.business.gov.au/Search/ResultsActive).
This endpoint **does not require authentication** and returns the same data
visible on the website.

**Limitations of the web-only approach:**
-   Cannot filter by employee count or ANZSIC code directly
-   Searches by company name keywords (industry keyword matching)
-   Address data is limited to state and postcode (no street address for most
    companies)
-   Rate-limited (use `--delay` to be respectful)

### ABR Web Services API (optional — requires free GUID)

The ABR offers a SOAP-based web service API that provides **enriched data**
including ANZSIC industry codes and employee count ranges. To use it:

1.  Register for a free GUID at:
    [https://abr.business.gov.au/Tools/WebServices](https://abr.business.gov.au/Tools/WebServices)
2.  Pass it with `--abn-guid YOUR_GUID_HERE`

With the API enabled, the scraper additionally collects:
-   **ANZSIC code** (e.g., "Q" for Health Care)
-   **ANZSIC description** (e.g., "Hospitals (Except Psychiatric Hospitals)")
-   **Employee count range** (e.g., "50-99", "100-199", "200-499")
-   **Full street address** (from the ABR's structured address data)

This allows filtering for companies with **50–1000 employees** — the sweet spot
for corporate mobile plan sales.

## Output CSV Format

| Column | Description |
|--------|-------------|
| `company_name` | Registered company name |
| `abn` | Australian Business Number (11 digits) |
| `acn` | Australian Company Number (9 digits, if registered) |
| `registered_address` | Main business location |
| `state` | State or territory |
| `postcode` | Postcode |
| `industry_search_term` | The industry filter key used |
| `industry_description` | Human-readable industry description |
| `anzsic_code` | ANZSIC division code (from API if GUID provided, or mapped from keyword) |
| `entity_type` | Entity type (filtered to "Entity Name (Company)") |
| `abn_status` | ABN status (always "Active") |
| `gst_status` | GST registration status |
| `employee_count_range` | Employee count range (only with `--abn-guid`) |
| `source_url` | Direct link to ABN Lookup page |

## Rate Limiting & Ethics

The scraper includes:
-   **Configurable delay** (`--delay` flag, default 1.5s between requests)
-   **Random jitter** (±50% added to each delay)
-   **Browser-like headers** to avoid being blocked
-   **Connection pooling** for efficiency

Please be respectful of the ABR service. For large-scale data needs, use the
official [ABN Bulk Extract](https://data.gov.au/data/dataset/abn-bulk-extract)
or register for the [ABR Web Services API](https://abr.business.gov.au/Tools/WebServices).

## Data Quality Notes

-   The scraper only includes **active ABNs** with **Entity Name** type
    (companies, not sole traders or business names)
-   Companies are found by **keyword matching** on registered names — some
    relevant companies may be missed if their name doesn't contain the keywords
-   Some companies may be shell entities, holding companies, or non-operational
    despite having active ABNs
-   For best results targeting companies with 50–1000 employees, use the
    `--abn-guid` option which enables employee count data from the ABR API

## Dependencies

-   `httpx` — HTTP client (already in project venv)
-   `beautifulsoup4` — HTML parsing (installed during setup)
-   `lxml` — Fast HTML parser (installed during setup)
-   `tqdm` — Progress bars (installed during setup)

Install with:

```bash
pip install httpx beautifulsoup4 lxml tqdm
```

## File Structure

```
lead_gen/
├── asic_scraper.py   # Main scraper script
├── leads.csv         # Default output (generated)
└── README.md         # This file
```
