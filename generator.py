"""Generate synthetic platform and bank transaction datasets with anomalies."""
import random
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

SEED = 42
random.seed(SEED)

USD_TO_INR = 83.5
BASE_DATE = datetime(2024, 3, 1)


def _rand_id(prefix: str, n: int) -> str:
    return f"{prefix}{n:04d}"


def _jitter_amount(amount: float, pct: float = 0.005) -> float:
    """Rounding / FX jitter."""
    return round(amount * (1 + random.uniform(-pct, pct)), 2)


def generate_datasets(num_txns: int = 40) -> dict[str, list[dict]]:
    platform_rows: list[dict] = []
    bank_rows: list[dict] = []

    for i in range(1, num_txns + 1):
        tid = _rand_id("TXN", i)
        amount_inr = round(random.uniform(500, 50_000), 2)
        txn_date = BASE_DATE + timedelta(days=random.randint(0, 27))
        currency = random.choice(["INR", "INR", "INR", "USD"])
        amount_platform = amount_inr if currency == "INR" else round(amount_inr / USD_TO_INR, 2)

        platform_rows.append({
            "txn_id": tid,
            "amount": amount_platform,
            "currency": currency,
            "date": txn_date.strftime("%Y-%m-%d"),
            "type": "CREDIT",
        })

        roll = random.random()

        if roll < 0.08:  # missing in bank
            continue
        if roll < 0.13:  # extra in bank (no platform record)
            bank_rows.append({
                "txn_id": _rand_id("EXT", i),
                "amount": round(random.uniform(100, 5000), 2),
                "currency": "INR",
                "date": txn_date.strftime("%Y-%m-%d"),
                "type": "CREDIT",
            })
            continue
        if roll < 0.18:  # delayed — bank books next month
            delayed_date = (txn_date + timedelta(days=random.randint(28, 35))).strftime("%Y-%m-%d")
            bank_rows.append({
                "txn_id": tid,
                "amount": amount_inr,
                "currency": "INR",
                "date": delayed_date,
                "type": "CREDIT",
            })
            continue
        if roll < 0.22:  # duplicate in bank
            bank_rows.append({"txn_id": tid, "amount": amount_inr, "currency": "INR",
                               "date": txn_date.strftime("%Y-%m-%d"), "type": "CREDIT"})
            bank_rows.append({"txn_id": tid, "amount": amount_inr, "currency": "INR",
                               "date": txn_date.strftime("%Y-%m-%d"), "type": "CREDIT"})
            continue
        if roll < 0.27:  # rounding diff
            bank_rows.append({"txn_id": tid, "amount": _jitter_amount(amount_inr),
                               "currency": "INR", "date": txn_date.strftime("%Y-%m-%d"), "type": "CREDIT"})
            continue
        if roll < 0.31:  # refund
            platform_rows[-1]["type"] = "REFUND"
            bank_rows.append({"txn_id": tid, "amount": amount_inr, "currency": "INR",
                               "date": txn_date.strftime("%Y-%m-%d"), "type": "DEBIT"})
            continue

        # normal match
        bank_rows.append({
            "txn_id": tid,
            "amount": amount_inr,
            "currency": "INR",
            "date": txn_date.strftime("%Y-%m-%d"),
            "type": "CREDIT",
        })

    return {"platform": platform_rows, "bank": bank_rows}
