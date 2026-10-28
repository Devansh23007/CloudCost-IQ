
from pathlib import Path
import random

import pandas as pd

# Reproducible dataset: the same seed produces the same data.
random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = "2026-07-01"
END_DATE = "2026-09-28"
NUM_RECORDS = 5000

PROVIDERS = {
    "AWS": {
        "regions": ["ap-south-1", "us-east-1", "eu-west-1"],
        "services": {
            "Compute": ("instance-hours", 0.08),
            "Object Storage": ("GB-months", 0.025),
            "Database": ("instance-hours", 0.12),
            "Networking": ("GB", 0.09),
        },
    },
    "Azure": {
        "regions": ["centralindia", "eastus", "westeurope"],
        "services": {
            "Compute": ("instance-hours", 0.075),
            "Object Storage": ("GB-months", 0.023),
            "Database": ("instance-hours", 0.115),
            "Networking": ("GB", 0.085),
        },
    },
    "GCP": {
        "regions": ["asia-south1", "us-central1", "europe-west1"],
        "services": {
            "Compute": ("instance-hours", 0.07),
            "Object Storage": ("GB-months", 0.02),
            "Database": ("instance-hours", 0.11),
            "Networking": ("GB", 0.08),
        },
    },
}

TEAMS = [
    "Data Engineering",
    "AI/ML",
    "Platform",
    "Analytics",
    "Product",
]

ACCOUNTS = {
    "AWS": ["AWS-1001", "AWS-1002"],
    "Azure": ["AZ-2001", "AZ-2002"],
    "GCP": ["GCP-3001", "GCP-3002"],
}

def generate_record(record_number, billing_date):
    provider = random.choice(list(PROVIDERS))
    provider_config = PROVIDERS[provider]

    service = random.choice(list(provider_config["services"]))
    usage_unit, base_price = provider_config["services"][service]

    usage = round(random.uniform(5, 500), 3)
    unit_price = round(
        base_price * random.uniform(0.90, 1.10), 5
    )

    gross_cost = round(usage * unit_price, 2)
    discount = round(
        gross_cost * random.choice([0, 0.05, 0.10, 0.15]), 2
    )
    credits = round(
        gross_cost * random.choice([0, 0, 0.02, 0.05]), 2
    )

    # Ensure net cost never becomes negative.
    discount = min(discount, gross_cost)
    credits = min(credits, gross_cost - discount)

    return {
        "record_id": f"BILL-{record_number:06d}",
        "billing_date": billing_date.strftime("%Y-%m-%d"),
        "cloud_provider": provider,
        "account_id": random.choice(ACCOUNTS[provider]),
        "service": service,
        "team": random.choice(TEAMS),
        "region": random.choice(provider_config["regions"]),
        "usage_quantity": usage,
        "usage_unit": usage_unit,
        "unit_price": unit_price,
        "gross_cost": gross_cost,
        "discount": discount,
        "credits": credits,
        "currency": "USD",
        "invoice_id": (
            f"INV-{billing_date.strftime('%Y-%m')}"
        ),
    }

def main():
    dates = pd.date_range(START_DATE, END_DATE, freq="D")

    records = [
        generate_record(i, random.choice(dates))
        for i in range(1, NUM_RECORDS + 1)
    ]

    df = pd.DataFrame(records)

    # Stable ordering makes inspection easier.
    df = df.sort_values(
        ["billing_date", "record_id"]
    ).reset_index(drop=True)

    output_path = RAW_DIR / "cloud_billing.csv"
    df.to_csv(output_path, index=False)

    print("CloudCost IQ billing data generated successfully.")
    print(f"File: {output_path}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(
        f"Date range: {df['billing_date'].min()} "
        f"to {df['billing_date'].max()}"
    )
    print(f"Providers: {sorted(df['cloud_provider'].unique())}")
    print(f"Teams: {df['team'].nunique()}")
    print(f"Services: {df['service'].nunique()}")
    print(f"Total gross cost: ${df['gross_cost'].sum():,.2f}")
    print(
        f"Total net cost: "
        f"${(df['gross_cost'] - df['discount'] - df['credits']).sum():,.2f}"
    )

if __name__ == "__main__":
    main()
