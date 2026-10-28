
from pathlib import Path
import os

import pandas as pd
import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = ROOT / "data" / "processed" / "cloud_billing_valid.csv"

load_dotenv(ROOT / ".env")

INSERT_SQL = """
    INSERT INTO raw.cloud_billing (
        record_id,
        billing_date,
        cloud_provider,
        account_id,
        service,
        team,
        region,
        usage_quantity,
        usage_unit,
        unit_price,
        gross_cost,
        discount,
        credits,
        currency,
        invoice_id
    )
    VALUES (
        %(record_id)s,
        %(billing_date)s,
        %(cloud_provider)s,
        %(account_id)s,
        %(service)s,
        %(team)s,
        %(region)s,
        %(usage_quantity)s,
        %(usage_unit)s,
        %(unit_price)s,
        %(gross_cost)s,
        %(discount)s,
        %(credits)s,
        %(currency)s,
        %(invoice_id)s
    )
    ON CONFLICT (record_id) DO NOTHING
"""


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Validated CSV not found: {INPUT_FILE}\n"
            "Run the ingestion pipeline first."
        )

    df = pd.read_csv(INPUT_FILE)

    if df.empty:
        print("No validated records to load.")
        return

    # The ingestion output includes source_row, which is audit metadata.
    # Only billing table columns are inserted.
    columns = [
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

    df = df[columns].copy()
    df["billing_date"] = pd.to_datetime(
        df["billing_date"], errors="raise"
    ).dt.date

    if df["record_id"].duplicated().any():
        raise ValueError("Duplicate record IDs found in input CSV.")

    connection_settings = {
        "dbname": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5434"),
        "connect_timeout": 5,
    }

    with psycopg.connect(**connection_settings) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT COUNT(*) AS count FROM raw.cloud_billing"
            )
            before_count = cur.fetchone()["count"]

            # executemany batches parameterized inserts safely.
            records = df.to_dict(orient="records")
            cur.executemany(INSERT_SQL, records)

            cur.execute(
                "SELECT COUNT(*) AS count FROM raw.cloud_billing"
            )
            after_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT
                    COUNT(*) AS row_count,
                    COALESCE(SUM(gross_cost), 0) AS gross_total,
                    COALESCE(SUM(discount), 0) AS discount_total,
                    COALESCE(SUM(credits), 0) AS credits_total,
                    COALESCE(
                        SUM(gross_cost - discount - credits), 0
                    ) AS net_total
                FROM raw.cloud_billing
            """)
            totals = cur.fetchone()

    print("PostgreSQL load completed.")
    print(f"Input rows: {len(df):,}")
    print(f"Rows inserted: {after_count - before_count:,}")
    print(f"Existing rows skipped: {len(df) - (after_count - before_count):,}")
    print(f"Total database rows: {totals['row_count']:,}")
    print(f"Gross cost: ${totals['gross_total']:,.2f}")
    print(f"Discounts: ${totals['discount_total']:,.2f}")
    print(f"Credits: ${totals['credits_total']:,.2f}")
    print(f"Net cost: ${totals['net_total']:,.2f}")


if __name__ == "__main__":
    main()
