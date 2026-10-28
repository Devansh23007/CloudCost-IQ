
from pathlib import Path
import os

import pandas as pd
import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "processed" / "cloud_billing_valid.csv"

load_dotenv(ROOT / ".env")

df = pd.read_csv(CSV_PATH)

df["net_cost"] = (
    df["gross_cost"] - df["discount"] - df["credits"]
)

with psycopg.connect(
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5434"),
) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*),
                COALESCE(SUM(gross_cost), 0),
                COALESCE(SUM(discount), 0),
                COALESCE(SUM(credits), 0),
                COALESCE(
                    SUM(gross_cost - discount - credits), 0
                )
            FROM raw.cloud_billing
        """)
        db_count, db_gross, db_discount, db_credits, db_net = (
            cur.fetchone()
        )

expected = {
    "count": len(df),
    "gross": round(df["gross_cost"].sum(), 2),
    "discount": round(df["discount"].sum(), 2),
    "credits": round(df["credits"].sum(), 2),
    "net": round(df["net_cost"].sum(), 2),
}

actual = {
    "count": db_count,
    "gross": round(float(db_gross), 2),
    "discount": round(float(db_discount), 2),
    "credits": round(float(db_credits), 2),
    "net": round(float(db_net), 2),
}

print("CSV totals:", expected)
print("Database totals:", actual)

if expected != actual:
    raise SystemExit(
        "RECONCILIATION FAILED. "
        "The CSV and database totals do not match."
    )

print("PASS: CSV and PostgreSQL totals match.")
