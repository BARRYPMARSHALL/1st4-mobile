"""
1st 4 Mobile — Synthetic Test Data Generator
Generates CSV files with known billing errors for pipeline testing.
"""

import csv
import random
from datetime import datetime, timedelta


def generate_test_csv(output_path: str, n_services: int = 50,
                      n_months: int = 3, error_rate: float = 0.10,
                      seed: int = 42):
    """
    Generate a test CSV file with known billing errors.
    
    Args:
        output_path: Where to write the CSV
        n_services: Number of unique services to simulate
        n_months: Number of billing months to generate
        error_rate: Fraction of services that will have intentional errors
        seed: Random seed for reproducibility
    
    Returns:
        dict: Summary of injected errors
    """
    random.seed(seed)
    
    fields = [
        "Account Number", "Service ID", "Service Type", "Plan Code",
        "Plan Name", "Description", "Charge Amount", "Usage (MB)",
        "Rate", "Period Start", "Period End", "Invoice #"
    ]
    
    # Generate base services
    services = []
    for i in range(n_services):
        svc_type = random.choice(["mobile", "mobile", "mobile", "data", "iot"])
        plan = {
            "mobile": ("MBP-50GB-POOL", "Mobile Business Pool 50GB", 45.00),
            "data": ("DATA-50GB-SHARED", "Data Only Shared 50GB", 35.00),
            "iot": ("IOT-1GB", "IoT Standard 1GB", 12.00),
        }[svc_type]
        
        services.append({
            "id": f"SVC-{i:04d}",
            "type": svc_type,
            "plan_code": plan[0],
            "plan_name": plan[1],
            "monthly_fee": plan[2],
            "has_error": random.random() < error_rate,
            "error_type": random.choice(["ghost", "rate", "rollback", "none"]),
        })
    
    rows = []
    errors_injected = {"ghost": 0, "rate": 0, "rollback": 0}
    
    for svc in services:
        for month_offset in range(n_months):
            period_start = datetime(2025, 1, 1) + timedelta(days=30 * month_offset)
            period_end = period_start + timedelta(days=29)
            period_start_str = period_start.strftime("%d/%m/%Y")
            period_end_str = period_end.strftime("%d/%m/%Y")
            invoice = f"INV-{month_offset + 1:03d}"
            
            monthly_fee = svc["monthly_fee"]
            usage = random.randint(100, 2000)
            
            # Inject errors
            if svc["has_error"] and svc["error_type"] == "ghost":
                usage = 0  # Ghost line — zero usage
                errors_injected["ghost"] += 1
            
            if svc["has_error"] and svc["error_type"] == "rate":
                monthly_fee = svc["monthly_fee"] * 1.22  # 22% overcharge
                if month_offset == 0:
                    errors_injected["rate"] += 1
            
            if svc["has_error"] and svc["error_type"] == "rollback":
                if month_offset >= 2:
                    # Rolled back to rack rate
                    monthly_fee = 105.00
                    if month_offset == 2:
                        errors_injected["rollback"] += 1
            
            # Monthly access charge
            rows.append([
                "ACC-001",  # Account Number
                svc["id"],  # Service ID
                svc["type"].title(),  # Service Type
                svc["plan_code"],  # Plan Code
                svc["plan_name"],  # Plan Name
                f"{svc['type'].title()} Plan Access Fee",  # Description
                f"${monthly_fee:.2f}",  # Charge Amount
                "",  # Usage
                "",  # Rate
                period_start_str,  # Period Start
                period_end_str,  # Period End
                invoice,  # Invoice #
            ])
            
            # Usage charge (if not ghost)
            if not (svc["has_error"] and svc["error_type"] == "ghost"):
                usage_amount = round(usage * 0.002, 2)
                rows.append([
                    "ACC-001",
                    svc["id"],
                    svc["type"].title(),
                    svc["plan_code"],
                    svc["plan_name"],
                    "Data Usage",
                    f"${usage_amount:.2f}",
                    str(usage),
                    "0.0020",
                    period_start_str,
                    period_end_str,
                    invoice,
                ])
    
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(rows)
    
    summary = {
        "total_services": n_services,
        "total_rows": len(rows),
        "errors_injected": errors_injected,
        "total_errors": sum(errors_injected.values()),
    }
    
    print(f"Test CSV generated: {output_path}")
    print(f"  Services: {n_services}, Rows: {len(rows)}")
    print(f"  Errors injected: {errors_injected}")
    
    return summary


if __name__ == "__main__":
    generate_test_csv("tests/fixtures/telstra_test.csv", n_services=100)
