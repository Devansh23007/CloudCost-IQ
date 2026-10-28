
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "processed"


def read_audit(name):
    path = OUTPUT_DIR / f"{name}_audit.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_clean_dataset_is_accepted():
    audit = read_audit("cloud_billing")

    assert audit["total_rows"] == 5000
    assert audit["accepted_rows"] == 5000
    assert audit["rejected_rows"] == 0


def test_corrupted_dataset_is_rejected_correctly():
    audit = read_audit("billing_quality_test")

    assert audit["total_rows"] == 106
    assert audit["accepted_rows"] == 100
    assert audit["rejected_rows"] == 6

    reasons = audit["rejection_counts"]

    assert reasons["duplicate_record_id"] >= 1
    assert reasons["missing_team"] >= 1
    assert reasons["negative_usage_quantity"] >= 1
    assert reasons["invalid_billing_date"] >= 1
    assert reasons["unsupported_currency"] >= 1


def test_rejected_rows_include_explanations():
    path = OUTPUT_DIR / "billing_quality_test_rejected.csv"
    rejected = pd.read_csv(path)

    assert len(rejected) == 6
    assert rejected["rejection_reasons"].notna().all()
    assert rejected["rejection_reasons"].str.len().gt(0).all()


def test_accepted_record_ids_are_unique():
    path = OUTPUT_DIR / "cloud_billing_valid.csv"
    valid = pd.read_csv(path)

    assert valid["record_id"].is_unique
