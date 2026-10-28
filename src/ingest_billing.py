
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

REQUIRED_COLUMNS = [
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

NUMERIC_COLUMNS = [
    "usage_quantity",
    "unit_price",
    "gross_cost",
    "discount",
    "credits",
]

ALLOWED_PROVIDERS = {"AWS", "Azure", "GCP"}
ALLOWED_CURRENCIES = {"USD"}


def validate_row(row, seen_ids):
    """Return a list of validation errors for one billing row."""
    errors = []

    # Required text fields
    text_columns = [
        "record_id",
        "cloud_provider",
        "account_id",
        "service",
        "team",
        "region",
        "usage_unit",
        "currency",
        "invoice_id",
    ]

    for column in text_columns:
        value = row[column]
        if pd.isna(value) or not str(value).strip():
            errors.append(f"missing_{column}")

    # Validate record ID uniqueness.
    record_id = row["record_id"]
    if pd.notna(record_id) and str(record_id).strip():
        record_id = str(record_id).strip()
        if record_id in seen_ids:
            errors.append("duplicate_record_id")
        else:
            # Reserve the ID even if another field in this row is invalid.
            seen_ids.add(record_id)

    # Validate provider and currency.
    if pd.notna(row["cloud_provider"]):
        if row["cloud_provider"] not in ALLOWED_PROVIDERS:
            errors.append("unsupported_cloud_provider")

    if pd.notna(row["currency"]):
        if row["currency"] not in ALLOWED_CURRENCIES:
            errors.append("unsupported_currency")

    # Validate billing date.
    try:
        date_value = pd.to_datetime(
            row["billing_date"], errors="raise"
        )
        if pd.isna(date_value):
            errors.append("missing_billing_date")
    except (ValueError, TypeError, OverflowError):
        errors.append("invalid_billing_date")

    # Validate numeric fields.
    numeric = {}
    for column in NUMERIC_COLUMNS:
        try:
            value = float(row[column])
            if pd.isna(value) or value == float("inf") or value == float("-inf"):
                raise ValueError
            numeric[column] = value
        except (ValueError, TypeError, OverflowError):
            errors.append(f"invalid_{column}")

    if len(numeric) == len(NUMERIC_COLUMNS):
        if numeric["usage_quantity"] < 0:
            errors.append("negative_usage_quantity")

        if any(numeric[c] < 0 for c in NUMERIC_COLUMNS[1:]):
            errors.append("negative_cost_or_price")

        # Costs should be calculated from usage multiplied by unit price.
        expected_gross = round(
            numeric["usage_quantity"] * numeric["unit_price"], 2
        )
        if abs(numeric["gross_cost"] - expected_gross) > 0.011:
            errors.append("gross_cost_mismatch")

        total_adjustments = numeric["discount"] + numeric["credits"]
        if total_adjustments > numeric["gross_cost"] + 0.011:
            errors.append("discounts_and_credits_exceed_gross_cost")

    return errors


def process_file(input_path, output_prefix):
    """Validate a CSV and save accepted, rejected, and audit outputs."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    if missing_columns:
        raise ValueError(
            f"CSV schema is missing required columns: {missing_columns}"
        )

    # Ignore unexpected extra columns for now, but retain the defined schema.
    df = df[REQUIRED_COLUMNS].copy()

    # Strip accidental whitespace from text fields.
    for column in df.select_dtypes(include=["object"]).columns:
        df[column] = df[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )

    # A seen ID is reserved on its first appearance. Later occurrences
    # are rejected, even if the first occurrence had another validation error.
    seen_ids = set()
    accepted = []
    rejected = []

    for index, row in df.iterrows():
        errors = validate_row(row, seen_ids)
        record = row.to_dict()
        record["source_row"] = int(index) + 2

        if errors:
            record["rejection_reasons"] = ";".join(errors)
            rejected.append(record)
        else:
            accepted.append(record)

    valid_df = pd.DataFrame(
        accepted, columns=REQUIRED_COLUMNS + ["source_row"]
    )
    rejected_df = pd.DataFrame(
        rejected,
        columns=REQUIRED_COLUMNS + ["source_row", "rejection_reasons"],
    )

    # Standardize dates and numeric types in accepted output.
    if not valid_df.empty:
        valid_df["billing_date"] = pd.to_datetime(
            valid_df["billing_date"]
        ).dt.strftime("%Y-%m-%d")

        for column in NUMERIC_COLUMNS:
            valid_df[column] = pd.to_numeric(valid_df[column])

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    valid_path = PROCESSED_DIR / f"{output_prefix}_valid.csv"
    rejected_path = PROCESSED_DIR / f"{output_prefix}_rejected.csv"
    audit_path = PROCESSED_DIR / f"{output_prefix}_audit.json"

    valid_df.to_csv(valid_path, index=False)
    rejected_df.to_csv(rejected_path, index=False)

    rejection_counts = {}
    if not rejected_df.empty:
        for reasons in rejected_df["rejection_reasons"]:
            for reason in reasons.split(";"):
                rejection_counts[reason] = (
                    rejection_counts.get(reason, 0) + 1
                )

    audit = {
        "source_file": input_path.name,
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_rows": len(df),
        "accepted_rows": len(valid_df),
        "rejected_rows": len(rejected_df),
        "rejection_counts": rejection_counts,
        "valid_output": str(valid_path.relative_to(ROOT)),
        "rejected_output": str(rejected_path.relative_to(ROOT)),
    }

    with audit_path.open("w", encoding="utf-8") as file:
        json.dump(audit, file, indent=2)

    print(f"\nFile processed: {input_path.name}")
    print(f"Total rows:     {len(df)}")
    print(f"Accepted rows:  {len(valid_df)}")
    print(f"Rejected rows:  {len(rejected_df)}")
    print(f"Valid output:   {valid_path}")
    print(f"Rejected output:{rejected_path}")
    print(f"Audit report:   {audit_path}")

    if rejection_counts:
        print("\nRejection reasons:")
        for reason, count in sorted(rejection_counts.items()):
            print(f"  {reason}: {count}")

    return audit


def main():
    parser = argparse.ArgumentParser(
        description="Validate CloudCost IQ billing CSV files."
    )
    parser.add_argument(
        "--input",
        default="cloud_billing.csv",
        help="CSV filename inside data/raw/",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Prefix for output files. Defaults to input filename.",
    )
    args = parser.parse_args()

    input_path = RAW_DIR / args.input
    output_prefix = args.prefix or input_path.stem

    process_file(input_path, output_prefix)


if __name__ == "__main__":
    main()
