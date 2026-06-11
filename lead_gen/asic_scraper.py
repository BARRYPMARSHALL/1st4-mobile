#!/usr/bin/env python3
"""
ASIC / ABR Company Scraper for Australian Corporate Telco Lead Generation.

Searches the Australian Business Register (ABR) public web interface to find
active Australian companies with valid ABNs, targeted by industry keywords.
Extracts company name, ABN, registered address, and industry classification.

Uses the public ABR website (no API key required) for company searches.
For ANZSIC codes and employee counts, the ABR Web Services API (free GUID
required) can be optionally configured.

Usage:
    python asic_scraper.py
    python asic_scraper.py --industries mining construction --max-companies 100
    python asic_scraper.py --output my_leads.csv --verbose
    python asic_scraper.py --abn-guid YOUR_GUID_HERE  # enables ANZSIC/employee data
"""

import argparse
import csv
import logging
import os
import random
import re
import sys
import time
from dataclasses import dataclass, asdict
from typing import Optional

import httpx
from bs4 import BeautifulSoup

# Try to import tqdm for progress bars
try:
    import tqdm

    TQDM_AVAILABLE = True
    tqdm = tqdm.tqdm
except ImportError:
    TQDM_AVAILABLE = False

logger = logging.getLogger("asic_scraper")

# ─── Default output path ────────────────────────────────────────────────
DEFAULT_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.csv")

# ─── Default industry keywords (mapped to ANZSIC divisions) ─────────────
DEFAULT_INDUSTRIES = {
    "mining": {
        "keywords": ["Mining", "Mine", "Resources", "Mineral"],
        "anzsic_code": "B",
        "description": "Mining",
    },
    "construction": {
        "keywords": ["Construction", "Building", "Civil", "Contractors"],
        "anzsic_code": "E",
        "description": "Construction",
    },
    "transport": {
        "keywords": ["Transport", "Logistics", "Freight", "Haulage", "Courier"],
        "anzsic_code": "I",
        "description": "Transport, Postal & Warehousing",
    },
    "healthcare": {
        "keywords": [
            "Medical",
            "Health",
            "Hospital",
            "Aged Care",
            "Pathology",
            "Radiology",
        ],
        "anzsic_code": "Q",
        "description": "Health Care & Social Assistance",
    },
    "professional_services": {
        "keywords": [
            "Consulting",
            "Professional Services",
            "Legal",
            "Accounting",
            "Engineering",
            "Architecture",
            "Management",
        ],
        "anzsic_code": "M",
        "description": "Professional, Scientific & Technical Services",
    },
    "wholesale": {
        "keywords": ["Wholesale", "Distributor", "Supply", "Merchant"],
        "anzsic_code": "F",
        "description": "Wholesale Trade",
    },
    "manufacturing": {
        "keywords": [
            "Manufacturing",
            "Manufacturer",
            "Fabrication",
            "Processing",
            "Production",
        ],
        "anzsic_code": "C",
        "description": "Manufacturing",
    },
    "retail": {
        "keywords": ["Retail", "Store", "Supermarket", "Department Store"],
        "anzsic_code": "G",
        "description": "Retail Trade",
    },
    "hospitality": {
        "keywords": [
            "Hotel",
            "Restaurant",
            "Cafe",
            "Hospitality",
            "Accommodation",
            "Resort",
        ],
        "anzsic_code": "H",
        "description": "Accommodation & Food Services",
    },
    "agriculture": {
        "keywords": [
            "Agriculture",
            "Farm",
            "Agribusiness",
            "Pastoral",
            "Viticulture",
        ],
        "anzsic_code": "A",
        "description": "Agriculture, Forestry & Fishing",
    },
}

# ─── Entity type codes from ABR ─────────────────────────────────────────
# We primarily want Entity Names (code 4) which represent actual companies.
ENTITY_TYPE_CODES = {
    "1": "Individual/Sole Trader",
    "2": "Trading Name",
    "3": "Partnership",
    "4": "Entity Name (Company)",
    "5": "Other Name",
    "6": "Government Entity",
    "7": "Business Name",
}

# ─── HTTP headers to mimic a real browser ───────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "DNT": "1",
}

ABR_BASE = "https://abr.business.gov.au"


# ─── Data model ─────────────────────────────────────────────────────────
@dataclass
class CompanyLead:
    """Represents a single company lead from the search."""

    company_name: str = ""
    abn: str = ""
    acn: str = ""
    registered_address: str = ""
    state: str = ""
    postcode: str = ""
    industry_search_term: str = ""
    industry_description: str = ""
    anzsic_code: str = ""
    entity_type: str = ""
    abn_status: str = ""
    gst_status: str = ""
    employee_count_range: str = ""
    source_url: str = ""


# ─── Scraper class ──────────────────────────────────────────────────────
class ASICCompanyScraper:
    """Scrapes the ABR public web interface to find Australian companies."""

    def __init__(
        self,
        output_file: str = DEFAULT_OUTPUT,
        max_companies: int = 200,
        delay: float = 1.5,
        abn_guid: Optional[str] = None,
        verbose: bool = False,
    ):
        self.output_file = output_file
        self.max_companies = max_companies
        self.delay = delay
        self.abn_guid = abn_guid
        self.verbose = verbose

        # Set up logging
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )

        # HTTP client with connection pooling and retries
        self.client = httpx.Client(
            headers=HEADERS,
            follow_redirects=True,
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

        self.leads: list[CompanyLead] = []
        self.seen_abns: set[str] = set()

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ─── Rate limiting ──────────────────────────────────────────────
    def _respectful_delay(self):
        """Sleep between requests to avoid rate limiting."""
        jitter = random.uniform(0.5, 1.5)
        time.sleep(self.delay * jitter)

    # ─── ABR Name Search ───────────────────────────────────────────
    def search_by_name(self, name: str) -> list[dict]:
        """
        Search ABR by company name. Returns list of parsed compressed results.
        Uses the active ABNs search endpoint.
        """
        url = f"{ABR_BASE}/Search/ResultsActive"
        params = {
            "SearchText": name,
            "AllNames": "False",
            "EntityName": "False",
            "BusinessName": "False",
            "NarrowSearch": "False",
            "SearchType": "ActiveAbns",
            "AllStates": "True",
        }

        logger.debug(f"Searching ABR for: {name}")
        try:
            resp = self.client.get(url, params=params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error searching '{name}': {e}")
            return []
        except httpx.RequestError as e:
            logger.warning(f"Request error searching '{name}': {e}")
            return []

        return self._parse_search_results(resp.text)

    def _parse_search_results(self, html: str) -> list[dict]:
        """
        Parse the ABR search results page.
        Extracts data from compressed hidden form fields.
        """
        soup = BeautifulSoup(html, "lxml")
        results = []

        # Find all compressed hidden fields
        for input_tag in soup.find_all("input", {"name": re.compile(r"Results\.NameItems\[\d+\]\.Compressed")}):
            value = input_tag.get("value", "")
            if not value:
                continue
            parts = value.split(",")
            if len(parts) < 12:
                continue

            try:
                abn_raw = parts[0].strip()
                abn_formatted = parts[1].strip() if len(parts) > 1 else ""
                # parts[2] = sequence number
                abn_status = parts[3].strip() if len(parts) > 3 else ""
                company_name = parts[5].strip() if len(parts) > 5 else ""
                current_flag = parts[6].strip() if len(parts) > 6 else ""
                entity_type_code = parts[7].strip() if len(parts) > 7 else ""
                entity_type_name = parts[8].strip() if len(parts) > 8 else ""
                # parts[9] = often empty (address line)
                postcode = parts[10].strip() if len(parts) > 10 else ""
                state = parts[11].strip() if len(parts) > 11 else ""

                # Only include active ABNs
                if abn_status.lower() != "active":
                    continue

                # Clean company name (remove excessive whitespace)
                company_name = re.sub(r"\s+", " ", company_name).strip()

                # Clean postcode and state (remove padding)
                postcode_clean = postcode.strip().split()[0] if postcode.strip() else ""
                state_clean = state.strip()

                results.append({
                    "abn": abn_raw,
                    "abn_formatted": abn_formatted,
                    "company_name": company_name,
                    "status": abn_status,
                    "entity_type_code": entity_type_code,
                    "entity_type_name": entity_type_name,
                    "postcode": postcode_clean,
                    "state": state_clean,
                    "current_flag": current_flag,
                })
            except (IndexError, ValueError) as e:
                logger.debug(f"Failed to parse compressed field: {e}")
                continue

        return results

    # ─── ABN Detail Page ────────────────────────────────────────────
    def get_abn_details(self, abn: str) -> dict:
        """
        Fetch the ABN detail page to get main business address and other details.
        """
        url = f"{ABR_BASE}/ABN/View"
        params = {"abn": abn}

        logger.debug(f"Fetching ABN details for: {abn}")
        try:
            resp = self.client.get(url, params=params)
            resp.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning(f"Error fetching ABN {abn}: {e}")
            return {}

        return self._parse_abn_details(resp.text)

    def _parse_abn_details(self, html: str) -> dict:
        """
        Parse the ABN detail page for address, GST status, entity type, ACN.
        """
        soup = BeautifulSoup(html, "lxml")
        details = {}

        # Find the ABN details table
        abn_table = soup.find("caption", string=lambda t: t and "ABN details" in t)
        if abn_table:
            table = abn_table.find_parent("table")
            if table:
                for row in table.find_all("tr"):
                    th = row.find("th")
                    td = row.find("td")
                    if th and td:
                        key = th.get_text(strip=True).lower().replace(":", "")
                        value = td.get_text(" ", strip=True)
                        details[key] = value

                        # Extract structured address
                        if "main business location" in key:
                            addr_div = td.find("div", itemprop="address")
                            if addr_div:
                                locality = addr_div.find("span", itemprop="addressLocality")
                                if locality:
                                    details["address_locality"] = locality.get_text(strip=True)

        # Extract ACN from ASIC registration section
        asic_caption = soup.find("caption", string=lambda t: t and "ASIC registration" in t)
        if asic_caption:
            table = asic_caption.find_parent("table")
            if table:
                asic_td = table.find("td")
                if asic_td:
                    text = asic_td.get_text(strip=True)
                    # ACN is usually 9 digits
                    acn_match = re.search(r"(\d{3}\s*\d{3}\s*\d{3})", text)
                    if acn_match:
                        details["acn"] = re.sub(r"\s+", "", acn_match.group(1))

        # Extract GST status
        for row in soup.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                key = th.get_text(strip=True).lower().replace(":", "")
                if "gst" in key:
                    details["gst_status"] = td.get_text(strip=True)

        return details

    # ─── ABR Web Services API (optional, requires GUID) ────────────
    def get_abn_via_api(self, abn: str) -> Optional[dict]:
        """
        Query the ABR SOAP API for enriched data (ANZSIC, employee count).
        Requires a registered GUID from ABR.
        Returns dict with extra data or None on failure.
        """
        if not self.abn_guid:
            return None

        # SOAP XML for SearchByABNv202001
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <SearchByABNv202001 xmlns="http://abr.business.gov.au/ABRXMLSearch/">
      <searchString>{abn}</searchString>
      <includeHistoricalDetails>N</includeHistoricalDetails>
      <authenticationGuid>{self.abn_guid}</authenticationGuid>
    </SearchByABNv202001>
  </soap:Body>
</soap:Envelope>"""

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "http://abr.business.gov.au/ABRXMLSearch/SearchByABNv202001",
        }

        try:
            resp = self.client.post(
                "https://abr.business.gov.au/abrxmlsearch/abrxmlsearch.asmx",
                content=soap_body,
                headers=headers,
                timeout=30.0,
            )
            resp.raise_for_status()
        except Exception as e:
            logger.debug(f"ABR API error for {abn}: {e}")
            return None

        return self._parse_api_response(resp.text)

    def _parse_api_response(self, xml: str) -> dict:
        """Parse SOAP XML response for ANZSIC and employee data."""
        soup = BeautifulSoup(xml, "lxml-xml")
        data = {}

        # Extract ANZSIC code and description
        anzsic_code_el = soup.find("anzsicCode")
        anzsic_desc_el = soup.find("anzsicDescription")
        if anzsic_code_el:
            data["anzsic_code"] = anzsic_code_el.get_text(strip=True)
        if anzsic_desc_el:
            data["anzsic_description"] = anzsic_desc_el.get_text(strip=True)

        # Extract employee count / persons count
        persons_count_el = soup.find("numberOfEmployees")
        persons_code_el = soup.find("numberOfEmployeesCode")
        persons_desc_el = soup.find("numberOfEmployeesDescription")
        if persons_count_el:
            data["employee_count_range"] = persons_count_el.get_text(strip=True)
        if persons_code_el:
            data["employee_code"] = persons_code_el.get_text(strip=True)
        if persons_desc_el:
            data["employee_description"] = persons_desc_el.get_text(strip=True)

        # Extract main business physical address from API
        addr_el = soup.find("mainBusinessPhysicalAddress")
        if addr_el:
            parts = []
            for tag in ["addressLine1", "addressLine2", "suburb", "state", "postcode"]:
                el = addr_el.find(tag)
                if el and el.get_text(strip=True):
                    parts.append(el.get_text(strip=True))
            if parts:
                data["registered_address"] = ", ".join(parts)

        # If no physical address, try postal address
        if not data.get("registered_address"):
            addr_el = soup.find("mainBusinessAddress")
            if addr_el:
                parts = []
                for tag in ["addressLine1", "addressLine2", "suburb", "state", "postcode"]:
                    el = addr_el.find(tag)
                    if el and el.get_text(strip=True):
                        parts.append(el.get_text(strip=True))
                if parts:
                    data["registered_address"] = ", ".join(parts)

        # Extract GST status
        gst_el = soup.find("gstStatus")
        if gst_el is not None:
            data["gst_status"] = gst_el.get_text(strip=True)

        return data

    # ─── Industry keyword search ────────────────────────────────────
    def search_industry(
        self,
        industry_key: str,
        industry_config: dict,
    ) -> list[CompanyLead]:
        """
        Search for companies in a specific industry using industry keywords.
        Returns filtered company leads.
        """
        industry_leads: list[CompanyLead] = []
        keywords = industry_config.get("keywords", [])
        industry_desc = industry_config.get("description", industry_key)
        anzsic_code = industry_config.get("anzsic_code", "")

        logger.info(
            f"Searching industry: {industry_desc} "
            f"(ANZSIC {anzsic_code}) — {len(keywords)} keyword groups"
        )

        for keyword in keywords:
            if len(industry_leads) >= self.max_companies:
                break

            # Search for the keyword alone
            results = self.search_by_name(keyword)
            logger.debug(
                f"  Keyword '{keyword}': {len(results)} results"
            )

            for result in results:
                if len(industry_leads) >= self.max_companies:
                    break

                abn_raw = result["abn"]
                if abn_raw in self.seen_abns:
                    continue

                # Filter for company-type entities (entity_type_code == "4")
                entity_code = result.get("entity_type_code", "")
                if entity_code != "4":
                    continue

                self.seen_abns.add(abn_raw)

                # Build lead
                lead = CompanyLead(
                    company_name=result["company_name"],
                    abn=abn_raw,
                    state=result.get("state", ""),
                    postcode=result.get("postcode", ""),
                    industry_search_term=industry_key,
                    industry_description=industry_desc,
                    anzsic_code=anzsic_code,
                    entity_type=ENTITY_TYPE_CODES.get(entity_code, entity_code),
                    abn_status=result.get("status", ""),
                )

                # Get detail page for address
                self._respectful_delay()
                details = self.get_abn_details(abn_raw)

                # Build address from available data
                address_parts = []
                if "address_locality" in details:
                    address_parts.append(details["address_locality"])
                else:
                    # Fall back to constructing from state/postcode
                    addr = ", ".join(
                        p for p in [lead.state, lead.postcode] if p
                    )
                    if addr:
                        address_parts.append(addr)
                lead.registered_address = ", ".join(address_parts)

                # Extract ACN
                lead.acn = details.get("acn", "")

                # Extract GST status
                gst = details.get("gst_status", "") or details.get("GST", "")
                if gst:
                    lead.gst_status = gst

                # If GUID available, get enriched data
                if self.abn_guid:
                    self._respectful_delay()
                    api_data = self.get_abn_via_api(abn_raw)
                    if api_data:
                        if api_data.get("registered_address"):
                            lead.registered_address = api_data["registered_address"]
                        if api_data.get("anzsic_code"):
                            lead.anzsic_code = api_data["anzsic_code"]
                        if api_data.get("anzsic_description"):
                            # Use the more specific description from API
                            pass
                        if api_data.get("employee_count_range"):
                            lead.employee_count_range = api_data["employee_count_range"]
                        if api_data.get("employee_description"):
                            lead.employee_count_range = api_data["employee_description"]
                        if api_data.get("gst_status"):
                            lead.gst_status = api_data["gst_status"]

                lead.source_url = (
                    f"{ABR_BASE}/ABN/View?abn={abn_raw}"
                )
                industry_leads.append(lead)

            self._respectful_delay()

        logger.info(
            f"  → {len(industry_leads)} company leads from {industry_desc}"
        )
        return industry_leads

    # ─── Main search orchestration ──────────────────────────────────
    def run(self, industries: dict[str, dict]) -> list[CompanyLead]:
        """Run the full search across all specified industries."""
        all_leads: list[CompanyLead] = []
        total_target = self.max_companies

        # Calculate target per industry
        industry_keys = list(industries.keys())
        per_industry = max(1, total_target // len(industry_keys))

        logger.info(
            f"Starting ASIC company scraper — "
            f"target: {total_target} companies across {len(industry_keys)} industries"
        )
        if self.abn_guid:
            logger.info("ABR API GUID provided — will fetch ANZSIC/employee data")
        else:
            logger.info(
                "No ABR API GUID — using web data only "
                "(pass --abn-guid for enriched data)"
            )
        logger.info(f"Output: {self.output_file}")
        logger.info("")

        # Wrap with tqdm if available
        if TQDM_AVAILABLE:
            import tqdm as _tqdm_mod
            iterator = _tqdm_mod.tqdm(industry_keys, desc="Industries", unit="industry")
        else:
            iterator = industry_keys

        for industry_key in iterator:
            if len(all_leads) >= total_target:
                break

            industry_config = industries[industry_key]
            # Temporarily adjust max for this industry
            remaining = total_target - len(all_leads)
            self.max_companies = min(per_industry, remaining)

            leads = self.search_industry(industry_key, industry_config)
            all_leads.extend(leads)

        logger.info(
            f"\nTotal leads collected: {len(all_leads)}"
        )
        return all_leads

    # ─── CSV Export ─────────────────────────────────────────────────
    def export_csv(self, leads: list[CompanyLead]):
        """Export leads to CSV file."""
        os.makedirs(os.path.dirname(self.output_file) or ".", exist_ok=True)

        fieldnames = [
            "company_name",
            "abn",
            "acn",
            "registered_address",
            "state",
            "postcode",
            "industry_search_term",
            "industry_description",
            "anzsic_code",
            "entity_type",
            "abn_status",
            "gst_status",
            "employee_count_range",
            "source_url",
        ]

        with open(self.output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for lead in leads:
                writer.writerow(asdict(lead))

        logger.info(f"Exported {len(leads)} leads to {self.output_file}")


# ─── CLI entry point ───────────────────────────────────────────────────
def parse_industries(industry_names: list[str]) -> dict:
    """Parse CLI industry flags into the industry config dict."""
    if not industry_names:
        return {
            k: v
            for k, v in DEFAULT_INDUSTRIES.items()
            if k
            in [
                "mining",
                "construction",
                "transport",
                "healthcare",
                "professional_services",
            ]
        }

    result = {}
    for name in industry_names:
        name = name.lower().replace(" ", "_")
        if name in DEFAULT_INDUSTRIES:
            result[name] = DEFAULT_INDUSTRIES[name]
        else:
            logger.warning(f"Unknown industry: '{name}'. Available: {list(DEFAULT_INDUSTRIES.keys())}")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="ASIC/ABR Company Scraper for Australian Corporate Telco Lead Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                          # Default: 200 leads, 5 industries
  %(prog)s --industries mining construction         # Specific industries only
  %(prog)s --max-companies 50 --output leads.csv    # Smaller batch, custom output
  %(prog)s --abn-guid ABCDEF12-... --verbose        # With ABR API for ANZSIC/employee data
        """,
    )
    parser.add_argument(
        "--industries",
        nargs="+",
        default=None,
        help=(
            "Industry filters (space-separated). "
            f"Options: {', '.join(DEFAULT_INDUSTRIES.keys())}. "
            "Default: mining, construction, transport, healthcare, professional_services"
        ),
    )
    parser.add_argument(
        "--max-companies",
        type=int,
        default=200,
        help="Maximum total companies to collect (default: 200)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Base delay in seconds between requests (default: 1.5)",
    )
    parser.add_argument(
        "--abn-guid",
        type=str,
        default=None,
        help="ABR Web Services API GUID for enriched data (ANZSIC, employee count)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    parser.add_argument(
        "--list-industries",
        action="store_true",
        help="List available industry filters and exit",
    )

    args = parser.parse_args()

    # Special: just list industries
    if args.list_industries:
        print("\nAvailable industry filters:\n")
        for key, cfg in DEFAULT_INDUSTRIES.items():
            print(f"  {key:25s}  →  {cfg['description']}  (ANZSIC {cfg['anzsic_code']})")
            print(f"  {'':25s}     Keywords: {', '.join(cfg['keywords'])}")
            print()
        return

    # Parse industry selection
    industries = parse_industries(args.industries)
    if not industries:
        logger.error("No valid industries selected. Use --list-industries to see options.")
        sys.exit(1)

    # Run scraper
    scraper = ASICCompanyScraper(
        output_file=args.output,
        max_companies=args.max_companies,
        delay=args.delay,
        abn_guid=args.abn_guid,
        verbose=args.verbose,
    )

    try:
        leads = scraper.run(industries)
        scraper.export_csv(leads)
    except KeyboardInterrupt:
        logger.warning("\nInterrupted. Saving partial results...")
        if scraper.leads:
            scraper.export_csv(scraper.leads)
        sys.exit(1)
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
