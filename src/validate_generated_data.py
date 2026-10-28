
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
csv_path = ROOT / "data" / "raw" / "cloud_billing.csv"

df = pd.read_csv(csv_path)

required_columns = [
    "record_id",
    "billing_date",
    "cloud_provider",
    "account_id",
    "service",
    "team",
    "region",
    "usage_quantity",
    "usage_unit",
    "unit_price",
    "gross_cost",
    "discount",
    "credits",
    "currency",
    "invoice_id",
]

assert list(df.columns) == required_columns, (
    "Unexpected column names or order."
)
assert len(df) == 5000, "Expected 5,000 records."
assert df["record_id"].is_unique, "Duplicate record IDs found."
assert not df[required_columns].isna().any().any(), (
    "Missing values found."
)
assert df["currency"].eq("USD").all(), (
    "Unexpected currency found."
)
assert pd.to_datetime(
    df["billing_date"], errors="raise"
).notna().all(), "Invalid billing dates found."

numeric_columns = [
    "usage_quantity",
    "unit_price",
    "gross_cost",
    "discount",
    "credits",
]

assert (df[numeric_columns] >= 0).all().all(), (
    "Negative numeric values found."
)
assert (df["discount"] + df["credits"] <= df["gross_cost"] + 0.011).all(), (
    "Discounts and credits exceed gross cost."
)

print("PASS: Main billing dataset validation")
print(f"Records: {len(df):,}")
print(f"Unique record IDs: {df['record_id'].nunique():,}")
print(f"Providers: {df['cloud_provider'].nunique()}")
print(f"Teams: {df['team'].nunique()}")
print(f"Services: {df['service'].nunique()}")
print("Currency: USD")
print("Missing values: none")
print("Negative numeric values: none")
