
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
raw_dir = ROOT / "data" / "raw"

source_path = raw_dir / "cloud_billing.csv"
output_path = raw_dir / "billing_quality_test.csv"

if not source_path.exists():
    raise FileNotFoundError(
        "Run src/generate_billing_data.py first."
    )

df = pd.read_csv(source_path)

# Keep a small, representative sample of valid records.
test_df = df.head(100).copy()

# Problem 1: duplicate an existing record.
duplicate = test_df.iloc[[0]].copy()

# Problem 2: missing team.
missing_team = test_df.iloc[[1]].copy()
missing_team["record_id"] = "TEST-MISSING-TEAM"
missing_team["team"] = None

# Problem 3: negative usage.
negative_usage = test_df.iloc[[2]].copy()
negative_usage["record_id"] = "TEST-NEGATIVE-USAGE"
negative_usage["usage_quantity"] = -50

# Problem 4: invalid date.
invalid_date = test_df.iloc[[3]].copy()
invalid_date["record_id"] = "TEST-INVALID-DATE"
invalid_date["billing_date"] = "not-a-date"

# Problem 5: unsupported currency.
invalid_currency = test_df.iloc[[4]].copy()
invalid_currency["record_id"] = "TEST-INVALID-CURRENCY"
invalid_currency["currency"] = "XYZ"

# Problem 6: negative gross cost.
negative_cost = test_df.iloc[[5]].copy()
negative_cost["record_id"] = "TEST-NEGATIVE-COST"
negative_cost["gross_cost"] = -10

test_df = pd.concat(
    [
        test_df,
        duplicate,
        missing_team,
        negative_usage,
        invalid_date,
        invalid_currency,
        negative_cost,
    ],
    ignore_index=True,
)
test_df.to_csv(output_path, index=False)

print("Data quality test dataset created.")
print(f"Output: {output_path}")
print(f"Total rows: {len(test_df)}")
print("Injected problems:")
print("- One duplicate record")
print("- One missing team")
print("- One negative usage quantity")
print("- One invalid billing date")
print("- One unsupported currency")
