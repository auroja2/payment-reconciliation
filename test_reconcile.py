"""Basic tests for generator and reconciler."""
import pytest
from generator import generate_datasets
from reconciler import reconcile


def test_generate_returns_both_datasets():
    data = generate_datasets(20)
    assert "platform" in data and "bank" in data
    assert len(data["platform"]) > 0


def test_reconcile_all_matched():
    platform = [{"txn_id": "T001", "amount": 1000.0, "currency": "INR",
                 "date": "2024-03-01", "type": "CREDIT"}]
    bank = [{"txn_id": "T001", "amount": 1000.0, "currency": "INR",
             "date": "2024-03-01", "type": "CREDIT"}]
    r = reconcile(platform, bank)
    assert r["results"][0]["status"] == "MATCHED"
    assert r["summary"]["matched"] == 1


def test_reconcile_missing_in_bank():
    platform = [{"txn_id": "T002", "amount": 500.0, "currency": "INR",
                 "date": "2024-03-01", "type": "CREDIT"}]
    r = reconcile(platform, [])
    assert r["results"][0]["status"] == "MISSING_IN_BANK"


def test_reconcile_extra_in_bank():
    bank = [{"txn_id": "T003", "amount": 999.0, "currency": "INR",
             "date": "2024-03-01", "type": "CREDIT"}]
    r = reconcile([], bank)
    assert r["results"][0]["status"] == "EXTRA_IN_BANK"


def test_reconcile_rounding_diff():
    platform = [{"txn_id": "T004", "amount": 1000.0, "currency": "INR",
                 "date": "2024-03-01", "type": "CREDIT"}]
    bank = [{"txn_id": "T004", "amount": 1001.5, "currency": "INR",
             "date": "2024-03-01", "type": "CREDIT"}]
    r = reconcile(platform, bank)
    assert r["results"][0]["status"] == "ROUNDING_DIFF"


def test_reconcile_amount_mismatch():
    platform = [{"txn_id": "T005", "amount": 1000.0, "currency": "INR",
                 "date": "2024-03-01", "type": "CREDIT"}]
    bank = [{"txn_id": "T005", "amount": 850.0, "currency": "INR",
             "date": "2024-03-01", "type": "CREDIT"}]
    r = reconcile(platform, bank)
    assert r["results"][0]["status"] == "AMOUNT_MISMATCH"


def test_reconcile_usd_conversion():
    platform = [{"txn_id": "T006", "amount": 12.0, "currency": "USD",
                 "date": "2024-03-01", "type": "CREDIT"}]  # 12 * 83.5 = 1002
    bank = [{"txn_id": "T006", "amount": 1002.0, "currency": "INR",
             "date": "2024-03-01", "type": "CREDIT"}]
    r = reconcile(platform, bank)
    assert r["results"][0]["status"] == "MATCHED"


def test_reconcile_duplicate():
    platform = [{"txn_id": "T007", "amount": 200.0, "currency": "INR",
                 "date": "2024-03-01", "type": "CREDIT"}]
    bank = [
        {"txn_id": "T007", "amount": 200.0, "currency": "INR", "date": "2024-03-01", "type": "CREDIT"},
        {"txn_id": "T007", "amount": 200.0, "currency": "INR", "date": "2024-03-01", "type": "CREDIT"},
    ]
    r = reconcile(platform, bank)
    assert r["results"][0]["status"] == "DUPLICATE_IN_BANK"


def test_reconcile_refund():
    platform = [{"txn_id": "T008", "amount": 300.0, "currency": "INR",
                 "date": "2024-03-01", "type": "REFUND"}]
    bank = [{"txn_id": "T008", "amount": 300.0, "currency": "INR",
             "date": "2024-03-01", "type": "DEBIT"}]
    r = reconcile(platform, bank)
    assert r["results"][0]["status"] == "REFUND_MATCHED"


def test_summary_match_rate():
    data = generate_datasets(30)
    r = reconcile(data["platform"], data["bank"])
    assert 0 <= r["summary"]["match_rate"] <= 100
